from __future__ import annotations

from alpha_app.core.pipeline import AlphaPipeline
from alpha_app.core.proposals import PROPOSALS


def test_open_card_auto_runs_pipeline_and_returns_post_payload() -> None:
    pipeline = AlphaPipeline(proposals=PROPOSALS)
    expanded = pipeline.open_card("deth_park")
    assert expanded.proposal.proposal_id == "deth_park"
    assert expanded.comments
    assert expanded.stage1_results
    assert expanded.insight.proposal_id == "deth_park"


def test_dashboard_data_contract_returns_chart_ready_series() -> None:
    pipeline = AlphaPipeline(proposals=PROPOSALS)
    overview, proposal = pipeline.build_dashboard_data(mode="advanced", proposal_id="nikis_pedestrian")
    assert overview.proposal_comparison
    assert overview.sentiment_by_proposal
    assert overview.trend_points
    assert proposal.sentiment_distribution
    assert proposal.stance_distribution
    assert proposal.argument_quality_distribution

