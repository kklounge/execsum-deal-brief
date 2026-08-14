from __future__ import annotations

from pydantic import BaseModel, Field


class Source(BaseModel):
    title: str
    url: str
    source_type: str = Field(
        description="One of: primary, reporting, expert, analysis"
    )
    publication_date: str


class ExpertInsight(BaseModel):
    name: str
    role: str
    organization: str
    insight: str
    source_title: str
    source_url: str
    publication_date: str
    potential_conflict: str


class DealAnalysis(BaseModel):
    rank: int = Field(ge=1, le=3)
    title: str
    category: str
    heat_label: str
    overview: str
    why_it_matters: list[str] = Field(min_length=2, max_length=4)
    expert_insights: list[ExpertInsight] = Field(max_length=2)
    ib_angles: list[str] = Field(min_length=1, max_length=4)
    sources: list[Source] = Field(min_length=2, max_length=5)


class DealBrief(BaseModel):
    issue_title: str
    issue_date: str
    issue_url: str
    report_date: str
    market_theme: str
    selection_methodology: str
    top_deals: list[DealAnalysis] = Field(min_length=1, max_length=3)
    other_deals: list[str]
    disclaimer: str

