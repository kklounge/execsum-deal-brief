from __future__ import annotations

import smtplib
from email.message import EmailMessage


def send_email(
    *,
    gmail_address: str,
    gmail_app_password: str,
    recipient: str,
    subject: str,
    text_body: str,
    html_body: str,
) -> None:
    message = EmailMessage()
    message["From"] = f"Exec Sum Deal Brief <{gmail_address}>"
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(gmail_address, gmail_app_password)
        smtp.send_message(message)

