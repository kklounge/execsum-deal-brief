from __future__ import annotations

from datetime import date

from .extractor import Issue
from .models import DealBrief


SYSTEM_PROMPT = """
You are a meticulous investment-banking news researcher. Produce a Chinese deal
brief while keeping company names and technical finance terms in English.

Hard rules:
- Treat the supplied Exec Sum Deal Flow as the candidate universe. Do not add a
  deal that is absent from it.
- Use web search for every selected deal. Prefer company announcements,
  regulatory filings, exchange notices and court/government documents, then
  Reuters, Bloomberg, FT, WSJ, CNBC and respected industry publications.
- Rank relative attention using independent coverage breadth, source diversity
  and authority, recency, transaction scale, strategic impact and capital-market
  discussion. Do not invent search-volume or social-engagement numbers. Deal
  size alone is not heat.
- Select at most three deals. Include every unselected candidate in other_deals.
- Separate confirmed facts, attributed views and your inference. If price,
  consideration, financing, status or timing is undisclosed, say so.
- Expert insights must be named, attributable and linked to a direct source.
  Never turn an anonymous source into an expert. Disclose when a speaker is a
  transaction party, regulator, investor or otherwise conflicted. If no reliable
  named insight exists, return an empty expert_insights list rather than inventing one.
- Each selected deal needs 2-5 clickable source URLs. Never fabricate or guess a URL.
- Do not copy long passages. Keep any direct quote under 20 words; prefer accurate
  paraphrase.
- The IB angle should address valuation, financing, synergies, regulation,
  execution risk, governance or competitive dynamics.
- This is research and interview preparation, not investment advice.
""".strip()


def research_issue(issue: Issue, *, model: str, report_date: date) -> DealBrief:
    # Import lazily so extraction and rendering tests do not require the SDK.
    from openai import OpenAI

    prompt = f"""
REPORT DATE: {report_date.isoformat()}
EXEC SUM ISSUE TITLE: {issue.title}
EXEC SUM ISSUE DATE: {issue.publication_date.isoformat()}
EXEC SUM ISSUE URL: {issue.url}

DEAL FLOW CANDIDATES:
{issue.deal_flow}

Research this exact candidate set and return the structured brief. The
selection_methodology field should explain the relative ranking without fake
precision. The disclaimer must state that the report is informational and not
investment advice.
""".strip()

    client = OpenAI()
    response = client.responses.parse(
        model=model,
        tools=[{"type": "web_search"}],
        tool_choice="required",
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        text_format=DealBrief,
        max_output_tokens=12000,
        store=False,
    )
    brief = response.output_parsed
    if brief is None:
        raise RuntimeError("OpenAI returned no structured brief")

    # Source-of-truth fields come from the scraper, not from generated text.
    brief.issue_title = issue.title
    brief.issue_date = issue.publication_date.isoformat()
    brief.issue_url = issue.url
    brief.report_date = report_date.isoformat()
    _validate_urls(brief, cited_urls=_collect_cited_urls(response))
    return brief


def _collect_cited_urls(response: object) -> set[str]:
    cited: set[str] = set()
    for output in getattr(response, "output", []):
        if getattr(output, "type", None) != "message":
            continue
        for content in getattr(output, "content", []):
            for annotation in getattr(content, "annotations", []):
                if getattr(annotation, "type", None) == "url_citation":
                    url = getattr(annotation, "url", None)
                    if url:
                        cited.add(_normalize_url(str(url)))
    return cited


def _normalize_url(url: str) -> str:
    from urllib.parse import urlparse, urlunparse

    parsed = urlparse(url)
    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip("/"),
            "",
            "",
            "",
        )
    )


def _validate_urls(brief: DealBrief, *, cited_urls: set[str]) -> None:
    from urllib.parse import urlparse

    urls: list[str] = []
    for deal in brief.top_deals:
        urls.extend(source.url for source in deal.sources)
        urls.extend(insight.source_url for insight in deal.expert_insights)
    invalid = [
        url
        for url in [brief.issue_url, *urls]
        if urlparse(url).scheme not in {"http", "https"} or not urlparse(url).netloc
    ]
    if invalid:
        raise ValueError(f"Model returned invalid source URLs: {invalid}")

    # Web-search responses expose URL citation annotations. When the SDK returns
    # them, require generated source URLs to match something actually retrieved.
    if cited_urls:
        uncited = [url for url in urls if _normalize_url(url) not in cited_urls]
        if uncited:
            raise ValueError(f"Model returned source URLs absent from citations: {uncited}")
