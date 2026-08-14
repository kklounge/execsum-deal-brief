# Security Policy

## Reporting a vulnerability

Please open a GitHub security advisory rather than a public issue when the
repository supports private vulnerability reporting.

## Secrets

This project must never store `OPENAI_API_KEY`, `GMAIL_APP_PASSWORD`, sender
addresses or recipient addresses in source control. Configure them as encrypted
GitHub Actions secrets. If a secret is ever committed, revoke or rotate it first;
removing it from the latest commit is not sufficient.

