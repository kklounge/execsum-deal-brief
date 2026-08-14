# Exec Sum Deal Brief

An open-source daily workflow that:

1. extracts the **Deal Flow** section from the latest public Exec Sum issue;
2. researches every candidate with OpenAI's Responses API and hosted web search;
3. ranks the three deals with the most relative attention;
4. generates a Chinese investment-banking brief with named expert insights and clickable sources; and
5. sends the brief through Gmail at **13:00 Asia/Hong_Kong** using GitHub Actions.

> This project is independent and is not affiliated with Exec Sum, Litquidity,
> OpenAI or Google. It only reads publicly accessible pages. Review the source
> site's terms and robots policy before adapting the scraper.

## What “hot” means

The ranking deliberately avoids fake precision. It weighs:

- breadth and diversity of independent coverage;
- authority of primary and secondary sources;
- recency;
- transaction scale and strategic impact; and
- capital-markets and industry discussion.

Deal size alone does not determine the ranking. Anonymous sources are never
presented as experts, and missing deal terms are labeled as undisclosed.

## Architecture

```text
Exec Sum archive
      ↓
public HTML extractor
      ↓
candidate Deal Flow list
      ↓
OpenAI Responses API + web_search
      ↓
Pydantic-validated DealBrief
      ↓
safe HTML renderer → Gmail SMTP
```

The OpenAI integration follows the official Responses API pattern with the
`web_search` tool and Structured Outputs. Web citations are rendered as visible,
clickable links in the email.

## Quick start

Requirements: Python 3.11+ and a Gmail account with 2-Step Verification.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install .

export OPENAI_API_KEY="..."
export GMAIL_ADDRESS="you@gmail.com"
export GMAIL_APP_PASSWORD="your-16-character-app-password"
export RECIPIENT_EMAIL="you@gmail.com"

python -m execsum_deal_brief.main --dry-run
python -m execsum_deal_brief.main
```

`--dry-run` still calls the OpenAI API but does not send email. It writes
`deal-brief-preview.html` for inspection.

## GitHub Actions setup

Create these repository secrets under **Settings → Secrets and variables →
Actions**:

| Secret | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | OpenAI API authentication |
| `GMAIL_ADDRESS` | Gmail sender address |
| `GMAIL_APP_PASSWORD` | Gmail App Password, not your normal password |
| `RECIPIENT_EMAIL` | Destination address; it may equal the sender |

Optional repository variable:

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_MODEL` | `gpt-5.5` | Responses API model override |

The included workflow runs at `05:00 UTC`, equivalent to `13:00` in Hong Kong.
GitHub Actions schedules are not guaranteed to start at the exact minute.
`workflow_dispatch` also lets you run a manual test from the Actions tab.

## Configuration

| Environment variable | Default |
| --- | --- |
| `EXEC_SUM_ARCHIVE_URL` | `https://litquidity.co/newsletter/exec-sum/` |
| `REPORT_TIMEZONE` | `Asia/Hong_Kong` |
| `MAX_ISSUE_AGE_DAYS` | `1` |
| `OPENAI_MODEL` | `gpt-5.5` |

If the source page is unavailable, Deal Flow is empty, or the latest issue is
too old, the workflow sends a short status email rather than presenting stale
deals as current.

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

The unit tests use local HTML fixtures and do not call Exec Sum, OpenAI or Gmail.

## 中文说明

这是一个可直接部署到 GitHub Actions 的每日交易简报工具。它会提取 Exec
Sum 最新一期的 Deal Flow，联网核验并筛选讨论度最高的三笔交易，以中文生成
交易概览、专家观点、IB 分析角度和来源链接，再通过 Gmail 发送。所有密钥均
通过 GitHub Secrets 配置，不应写入代码或提交记录。

## Security and responsible use

- Never commit API keys, Gmail passwords or recipient addresses.
- Use a dedicated Gmail App Password and rotate it if exposed.
- The generated brief can contain mistakes; verify material facts against the
  linked primary sources before relying on it.
- Respect publisher terms, rate limits and copyright. The project extracts
  concise deal facts and does not republish full articles.

## License

MIT. See [LICENSE](LICENSE).

