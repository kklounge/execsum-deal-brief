import unittest

from execsum_deal_brief.models import DealAnalysis, DealBrief, Source
from execsum_deal_brief.renderer import render_html


class RendererTests(unittest.TestCase):
    def test_escapes_generated_text(self) -> None:
        brief = DealBrief(
            issue_title="Issue <script>alert(1)</script>",
            issue_date="2026-08-13",
            issue_url="https://example.com/issue",
            report_date="2026-08-14",
            market_theme="Theme",
            selection_methodology="Method",
            top_deals=[
                DealAnalysis(
                    rank=1,
                    title="Buyer < Target",
                    category="M&A",
                    heat_label="High",
                    overview="Overview",
                    why_it_matters=["One", "Two"],
                    expert_insights=[],
                    ib_angles=["Valuation"],
                    sources=[
                        Source(
                            title="Primary",
                            url="https://example.com/a",
                            source_type="primary",
                            publication_date="2026-08-13",
                        ),
                        Source(
                            title="Reuters",
                            url="https://example.com/b",
                            source_type="reporting",
                            publication_date="2026-08-13",
                        ),
                    ],
                )
            ],
            other_deals=[],
            disclaimer="Not investment advice",
        )
        result = render_html(brief)
        self.assertNotIn("<script>", result)
        self.assertIn("Issue &lt;script&gt;", result)
        self.assertIn("Buyer &lt; Target", result)


if __name__ == "__main__":
    unittest.main()

