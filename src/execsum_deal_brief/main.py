from __future__ import annotations

import argparse
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from .config import Config
from .extractor import get_latest_issue
from .mailer import send_email
from .renderer import render_html, render_status_html, render_text
from .researcher import research_issue


LOGGER = logging.getLogger("execsum_deal_brief")


def run(*, dry_run: bool = False, issue_url: str | None = None) -> int:
    config = Config.from_env(require_delivery=not dry_run)
    local_now = datetime.now(ZoneInfo(config.report_timezone))
    report_date = local_now.date()

    try:
        issue = get_latest_issue(config.archive_url, issue_url=issue_url)
    except Exception as exc:
        LOGGER.exception("Could not extract the latest Exec Sum issue")
        if dry_run:
            raise
        _send_status(config, report_date.isoformat(), f"无法提取最新一期：{exc}")
        return 1

    issue_age = (report_date - issue.publication_date).days
    if issue_age < 0 or issue_age > config.max_issue_age_days:
        message = (
            f"最新可用一期为 {issue.publication_date.isoformat()}，"
            f"与报告日相差 {issue_age} 天，因此本次未生成交易摘要。"
        )
        if dry_run:
            print(message)
            return 0
        _send_status(config, report_date.isoformat(), message)
        return 0

    brief = research_issue(issue, model=config.model, report_date=report_date)
    html_body = render_html(brief)
    text_body = render_text(brief)
    subject = f"Exec Sum Deal Brief｜{report_date.isoformat()}｜Top {len(brief.top_deals)}"

    if dry_run:
        with open("deal-brief-preview.html", "w", encoding="utf-8") as handle:
            handle.write(html_body)
        print(text_body)
        LOGGER.info("Wrote deal-brief-preview.html; no email was sent")
        return 0

    send_email(
        gmail_address=config.gmail_address,
        gmail_app_password=config.gmail_app_password,
        recipient=config.recipient_email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )
    LOGGER.info("Sent %s to %s", subject, config.recipient_email)
    return 0


def _send_status(config: Config, report_date: str, message: str) -> None:
    subject = f"Exec Sum Deal Brief｜{report_date}｜状态通知"
    send_email(
        gmail_address=config.gmail_address,
        gmail_app_password=config.gmail_app_password,
        recipient=config.recipient_email,
        subject=subject,
        text_body=f"{message}\nChecked: {config.archive_url}",
        html_body=render_status_html(report_date, message, config.archive_url),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Send the daily Exec Sum deal brief")
    parser.add_argument("--dry-run", action="store_true", help="Render locally without email")
    parser.add_argument("--issue-url", help="Analyze a specific public issue URL")
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    raise SystemExit(run(dry_run=args.dry_run, issue_url=args.issue_url))


if __name__ == "__main__":
    main()

