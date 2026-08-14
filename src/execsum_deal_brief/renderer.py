from __future__ import annotations

from html import escape
from urllib.parse import urlparse

from .models import DealBrief, Source


def _safe_url(url: str) -> str:
    parsed = urlparse(url)
    return url if parsed.scheme in {"http", "https"} and parsed.netloc else "#"


def _source_link(source: Source) -> str:
    label = f"{source.title} ({source.publication_date})"
    return f'<a href="{escape(_safe_url(source.url), quote=True)}">{escape(label)}</a>'


def render_html(brief: DealBrief) -> str:
    deal_sections: list[str] = []
    for deal in sorted(brief.top_deals, key=lambda item: item.rank):
        why = "".join(f"<li>{escape(item)}</li>" for item in deal.why_it_matters)
        ib_angles = "".join(f"<li>{escape(item)}</li>" for item in deal.ib_angles)
        if deal.expert_insights:
            insights = "".join(
                (
                    "<li><b>"
                    + escape(f"{item.name}｜{item.role}, {item.organization}")
                    + ":</b> "
                    + escape(item.insight)
                    + " <i>利益/立场说明："
                    + escape(item.potential_conflict)
                    + "</i> "
                    + f'<a href="{escape(_safe_url(item.source_url), quote=True)}">'
                    + escape(f"来源：{item.source_title} ({item.publication_date})")
                    + "</a></li>"
                )
                for item in deal.expert_insights
            )
        else:
            insights = "<li>暂无可核实的具名专家观点。</li>"
        sources = " · ".join(_source_link(source) for source in deal.sources)

        deal_sections.append(
            f"""
            <hr style="border:0;border-top:1px solid #e6eaf0;margin:26px 0">
            <h2 style="font-size:20px;margin:0 0 8px;color:#132a55">
              {deal.rank}｜{escape(deal.title)}
            </h2>
            <div style="font-size:13px;color:#667085;margin-bottom:12px">
              {escape(deal.category)}｜讨论热度：{escape(deal.heat_label)}
            </div>
            <p><b>交易概览：</b>{escape(deal.overview)}</p>
            <p><b>为什么受到关注：</b></p><ul>{why}</ul>
            <p><b>专家 insights：</b></p><ul>{insights}</ul>
            <p><b>IB 视角：</b></p><ul>{ib_angles}</ul>
            <p style="font-size:13px"><b>Sources：</b>{sources}</p>
            """
        )

    other_deals = "".join(f"<li>{escape(item)}</li>" for item in brief.other_deals)
    issue_url = escape(_safe_url(brief.issue_url), quote=True)
    return f"""
    <div style="margin:0;background:#f5f7fa;padding:24px;font-family:Arial,'PingFang SC','Microsoft YaHei',sans-serif;color:#172033;line-height:1.65">
      <div style="max-width:760px;margin:0 auto;background:#fff;border:1px solid #e5e9f0;border-radius:14px;overflow:hidden">
        <div style="background:#14213d;color:#fff;padding:26px 30px">
          <div style="font-size:12px;letter-spacing:1.5px;color:#a8c4ff">EXEC SUM DEAL BRIEF</div>
          <div style="font-size:27px;font-weight:700;margin-top:5px">今日最受关注的交易</div>
          <div style="font-size:14px;color:#d9e4ff;margin-top:5px">
            报告日期：{escape(brief.report_date)}｜Exec Sum：{escape(brief.issue_date)}
          </div>
        </div>
        <div style="padding:24px 30px">
          <div style="background:#eef4ff;border-left:4px solid #2f6fed;padding:14px 16px;border-radius:6px">
            <b>今日市场基调</b><br>{escape(brief.market_theme)}
          </div>
          <p style="font-size:12px;color:#667085"><b>筛选方法：</b>{escape(brief.selection_methodology)}</p>
          {''.join(deal_sections)}
          <hr style="border:0;border-top:1px solid #e6eaf0;margin:28px 0">
          <h2 style="font-size:18px;color:#132a55">其他 Deal Flow</h2>
          <ul>{other_deals}</ul>
          <p style="font-size:13px"><b>Exec Sum 原文：</b>
            <a href="{issue_url}">{escape(brief.issue_title)}</a>
          </p>
          <div style="margin-top:24px;padding:13px 15px;background:#fff8e8;border:1px solid #f3dfaa;border-radius:7px;font-size:12px;color:#6f5410">
            {escape(brief.disclaimer)}
          </div>
        </div>
      </div>
    </div>
    """.strip()


def render_text(brief: DealBrief) -> str:
    lines = [
        f"Exec Sum Deal Brief | {brief.report_date}",
        f"Source issue: {brief.issue_title} ({brief.issue_date})",
        brief.issue_url,
        "",
        "今日市场基调",
        brief.market_theme,
        "",
    ]
    for deal in sorted(brief.top_deals, key=lambda item: item.rank):
        lines.extend(
            [
                f"{deal.rank}. {deal.title}",
                f"交易概览：{deal.overview}",
                "为什么受到关注：",
                *[f"- {item}" for item in deal.why_it_matters],
                "专家 insights：",
            ]
        )
        if deal.expert_insights:
            lines.extend(
                f"- {item.name} ({item.role}, {item.organization}): {item.insight} | {item.source_url}"
                for item in deal.expert_insights
            )
        else:
            lines.append("- 暂无可核实的具名专家观点。")
        lines.extend(["IB 视角：", *[f"- {item}" for item in deal.ib_angles], ""])
    lines.extend(["其他 Deal Flow：", *[f"- {item}" for item in brief.other_deals]])
    return "\n".join(lines)


def render_status_html(report_date: str, message: str, checked_url: str) -> str:
    return (
        "<div style=\"font-family:Arial,'Microsoft YaHei',sans-serif;line-height:1.6\">"
        f"<h2>Exec Sum Deal Brief｜{escape(report_date)}｜状态通知</h2>"
        f"<p>{escape(message)}</p>"
        f'<p>已检查：<a href="{escape(_safe_url(checked_url), quote=True)}">'
        f"{escape(checked_url)}</a></p>"
        "<p>系统没有使用旧交易冒充当日内容。</p></div>"
    )
