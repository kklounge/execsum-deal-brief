from __future__ import annotations

import html as html_lib
import re
from dataclasses import dataclass
from datetime import date, datetime
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


USER_AGENT = (
    "Mozilla/5.0 (compatible; ExecSumDealBrief/0.1; "
    "+https://github.com/kklounge/execsum-deal-brief)"
)


@dataclass(frozen=True)
class Issue:
    title: str
    publication_date: date
    url: str
    deal_flow: str


class _ArchiveParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._heading_tag: str | None = None
        self._heading_text: list[str] = []
        self._anchor_href: str | None = None
        self._anchor_text: list[str] = []
        self.in_recent_archive = False
        self.recent_links: list[tuple[str, str]] = []
        self.all_links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag in {"h1", "h2", "h3", "h4"}:
            self._heading_tag = tag
            self._heading_text = []
        elif tag == "a":
            self._anchor_href = attrs_dict.get("href")
            self._anchor_text = []

    def handle_data(self, data: str) -> None:
        if self._heading_tag:
            self._heading_text.append(data)
        if self._anchor_href is not None:
            self._anchor_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._heading_tag == tag:
            heading = " ".join(self._heading_text).strip().lower()
            if "more from the archive" in heading or "latest issues" in heading:
                self.in_recent_archive = True
            self._heading_tag = None
            self._heading_text = []
        if tag == "a" and self._anchor_href is not None:
            item = (self._anchor_href, " ".join(self._anchor_text).strip())
            self.all_links.append(item)
            if self.in_recent_archive:
                self.recent_links.append(item)
            self._anchor_href = None
            self._anchor_text = []


class _BlockParser(HTMLParser):
    BLOCK_TAGS = {"h1", "h2", "h3", "h4", "p", "li"}
    VOID_TAGS = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[tuple[str, str]] = []
        self._active_tag: str | None = None
        self._depth = 0
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._active_tag is None and tag in self.BLOCK_TAGS:
            self._active_tag = tag
            self._depth = 1
            self._text = []
        elif self._active_tag is not None and tag not in self.VOID_TAGS:
            self._depth += 1

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        return

    def handle_data(self, data: str) -> None:
        if self._active_tag is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._active_tag is None:
            return
        self._depth -= 1
        if self._depth == 0:
            text = re.sub(r"\s+", " ", " ".join(self._text)).strip()
            if text:
                self.blocks.append((self._active_tag, text))
            self._active_tag = None
            self._text = []


def fetch_html(url: str, *, timeout: int = 30) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        content_type = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(content_type, errors="replace")


def _is_issue_url(url: str, archive_url: str) -> bool:
    parsed = urlparse(urljoin(archive_url, url))
    archive_host = urlparse(archive_url).netloc
    if parsed.scheme not in {"http", "https"} or parsed.netloc != archive_host:
        return False
    path = parsed.path.rstrip("/")
    excluded = {
        "",
        "/articles",
        "/about",
        "/investments",
        "/recruiting",
        "/partnerships",
        "/newsletter/exec-sum",
        "/newsletter/crypto-sum",
    }
    return path not in excluded and path.count("/") == 1


def parse_archive_candidates(archive_html: str, archive_url: str) -> list[str]:
    parser = _ArchiveParser()
    parser.feed(archive_html)
    links = parser.recent_links or parser.all_links
    result: list[str] = []
    for href, _title in links:
        absolute = urljoin(archive_url, href)
        if _is_issue_url(absolute, archive_url) and absolute not in result:
            result.append(absolute)
    return result


_MONTHS = {
    month: number
    for number, month in enumerate(
        [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ],
        start=1,
    )
}


def _extract_date(raw_html: str) -> date:
    plain = html_lib.unescape(re.sub(r"<[^>]+>", " ", raw_html))
    match = re.search(
        r"\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(20\d{2})\b",
        plain,
    )
    if match:
        day, month, year = match.groups()
        return date(int(year), _MONTHS[month], int(day))

    iso_match = re.search(r"\b(20\d{2})-(\d{2})-(\d{2})\b", raw_html)
    if iso_match:
        return datetime.strptime(iso_match.group(0), "%Y-%m-%d").date()
    raise ValueError("Could not identify the issue publication date")


def parse_issue_html(issue_html: str, issue_url: str) -> Issue:
    parser = _BlockParser()
    parser.feed(issue_html)
    blocks = parser.blocks

    title = next((text for tag, text in blocks if tag == "h1"), "Exec Sum")
    start = next(
        (
            index
            for index, (tag, text) in enumerate(blocks)
            if tag.startswith("h") and text.strip().lower() == "deal flow"
        ),
        None,
    )
    if start is None:
        raise ValueError("The latest issue does not contain a Deal Flow section")

    lines: list[str] = []
    for tag, text in blocks[start + 1 :]:
        if tag == "h1":
            break
        if "access the complete vc deal flow" in text.lower():
            continue
        if tag == "li":
            lines.append(f"- {text}")
        else:
            if lines and lines[-1] != "":
                lines.append("")
            lines.append(text)

    deal_flow = "\n".join(lines).strip()
    if not deal_flow or "- " not in deal_flow:
        raise ValueError("Deal Flow was found but no deals could be extracted")

    return Issue(
        title=title,
        publication_date=_extract_date(issue_html),
        url=issue_url,
        deal_flow=deal_flow,
    )


def get_latest_issue(archive_url: str, *, issue_url: str | None = None) -> Issue:
    if issue_url:
        return parse_issue_html(fetch_html(issue_url), issue_url)

    archive_html = fetch_html(archive_url)
    candidates = parse_archive_candidates(archive_html, archive_url)
    if not candidates:
        raise ValueError("No public Exec Sum issue links were found in the archive")

    errors: list[str] = []
    for candidate in candidates[:5]:
        try:
            return parse_issue_html(fetch_html(candidate), candidate)
        except Exception as exc:  # Continue past non-issue cards in the archive.
            errors.append(f"{candidate}: {exc}")
    raise ValueError("No usable issue found. " + " | ".join(errors))
