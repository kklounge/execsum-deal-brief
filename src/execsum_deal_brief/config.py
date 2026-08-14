from __future__ import annotations

import os
from dataclasses import dataclass


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


@dataclass(frozen=True)
class Config:
    archive_url: str
    model: str
    report_timezone: str
    max_issue_age_days: int
    gmail_address: str
    gmail_app_password: str
    recipient_email: str

    @classmethod
    def from_env(cls, *, require_delivery: bool = True) -> "Config":
        gmail_address = os.getenv("GMAIL_ADDRESS", "").strip()
        gmail_app_password = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")
        recipient_email = os.getenv("RECIPIENT_EMAIL", gmail_address).strip()

        if require_delivery:
            gmail_address = _required("GMAIL_ADDRESS")
            gmail_app_password = _required("GMAIL_APP_PASSWORD").replace(" ", "")
            recipient_email = os.getenv("RECIPIENT_EMAIL", gmail_address).strip()
            if not recipient_email:
                raise ValueError("RECIPIENT_EMAIL cannot be empty")

        return cls(
            archive_url=os.getenv(
                "EXEC_SUM_ARCHIVE_URL",
                "https://litquidity.co/newsletter/exec-sum/",
            ).strip(),
            model=os.getenv("OPENAI_MODEL", "gpt-5.5").strip(),
            report_timezone=os.getenv("REPORT_TIMEZONE", "Asia/Hong_Kong").strip(),
            max_issue_age_days=int(os.getenv("MAX_ISSUE_AGE_DAYS", "1")),
            gmail_address=gmail_address,
            gmail_app_password=gmail_app_password,
            recipient_email=recipient_email,
        )

