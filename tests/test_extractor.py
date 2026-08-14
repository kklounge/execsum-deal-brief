from pathlib import Path
import unittest

from execsum_deal_brief.extractor import parse_archive_candidates, parse_issue_html


FIXTURES = Path(__file__).parent / "fixtures"


class ExtractorTests(unittest.TestCase):
    def test_prefers_recent_archive_section(self) -> None:
        html = (FIXTURES / "archive.html").read_text(encoding="utf-8")
        result = parse_archive_candidates(
            html, "https://litquidity.co/newsletter/exec-sum/"
        )
        self.assertEqual(result[0], "https://litquidity.co/latest-issue/")
        self.assertNotIn("https://litquidity.co/old-feature/", result)

    def test_extracts_only_deal_flow(self) -> None:
        html = (FIXTURES / "issue.html").read_text(encoding="utf-8")
        issue = parse_issue_html(html, "https://litquidity.co/latest-issue/")
        self.assertEqual(issue.title, "Example Exec Sum")
        self.assertEqual(issue.publication_date.isoformat(), "2026-08-13")
        self.assertIn("Buyer agreed to acquire Target", issue.deal_flow)
        self.assertIn("Startup raised a $100M Series C", issue.deal_flow)
        self.assertNotIn("must not be extracted", issue.deal_flow)


if __name__ == "__main__":
    unittest.main()

