from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal

Sentiment = Literal["positive", "neutral", "negative"]
Stance = Literal["for", "neutral", "against"]
DashboardMode = Literal["basic", "advanced"]
ProposalStatus = Literal["planned", "active", "delayed", "completed"]
ServiceType = Literal["water", "electricity", "traffic", "waste", "telecom"]


@dataclass(frozen=True)
class ProposalLink:
    label: str
    url: str


@dataclass(frozen=True)
class Proposal:
    proposal_id: str
    title: str
    municipality: str
    short_description: str
    long_description: str
    image_url: str
    status: ProposalStatus
    start_date: date
    end_date: date
    budget_eur: int
    affected_areas: list[str]
    affected_services: list[ServiceType]
    links: list[ProposalLink]
    map_polygon_geojson: dict[str, object]


@dataclass(frozen=True)
class CommentEvent:
    municipality_id: str
    proposal_id: str
    comment_id: str
    author_name: str
    comment_text: str
    reactions: dict[str, int]
    submitted_at: datetime


@dataclass(frozen=True)
class Stage1Result:
    comment_id: str
    proposal_id: str
    sentiment: Sentiment
    stance: Stance
    irony_flag: bool
    argument_quality_score: float
    confidence: float
    tags: list[str] = field(default_factory=list)
    agent_scores: dict[str, float] = field(default_factory=dict)
    agent_labels: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Stage2Insight:
    municipality_id: str
    proposal_id: str
    topics: list[str]
    trend_summary: str
    executive_summary: str
    generated_at: datetime


@dataclass(frozen=True)
class ProposalCardViewModel:
    proposal_id: str
    title: str
    status: ProposalStatus
    short_description: str
    image_url: str
    comments_total: int
    total_reactions: int
    support_ratio: float


@dataclass(frozen=True)
class ProposalExpandedViewModel:
    proposal: Proposal
    comments: list[CommentEvent]
    reactions: dict[str, int]
    stage1_results: list[Stage1Result]
    insight: Stage2Insight


@dataclass(frozen=True)
class DashboardOverviewSeries:
    proposal_comparison: list[dict[str, object]]
    sentiment_by_proposal: list[dict[str, object]]
    trend_points: list[dict[str, object]]
    service_impact: list[dict[str, object]]
    insight_line: str
    quality_telemetry: list[dict[str, object]] = field(default_factory=list)


@dataclass(frozen=True)
class DashboardProposalSeries:
    proposal_id: str
    sentiment_distribution: list[dict[str, object]]
    stance_distribution: list[dict[str, object]]
    reaction_velocity: list[dict[str, object]]
    topic_prevalence: list[dict[str, object]]
    argument_quality_distribution: list[dict[str, object]]
    insight_line: str
    correction_by_indicator: list[dict[str, object]] = field(default_factory=list)
    review_state_mix: list[dict[str, object]] = field(default_factory=list)
    review_lag_points: list[dict[str, object]] = field(default_factory=list)

