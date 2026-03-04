from __future__ import annotations

from alpha_app.core.pipeline import AlphaPipeline
from alpha_app.core.proposals import PROPOSALS


def test_reviewer_metrics_exist_after_refresh() -> None:
    pipeline = AlphaPipeline(proposals=PROPOSALS)
    pipeline.open_card("deth_park")

    metrics = pipeline.review_metrics.get("deth_park", {})
    assert metrics
    assert "correction_rate" in metrics
    assert "indicator_rates" in metrics


def test_dashboard_contract_includes_quality_telemetry() -> None:
    pipeline = AlphaPipeline(proposals=PROPOSALS)
    overview, proposal = pipeline.build_dashboard_data(mode="basic", proposal_id="metro_west")

    assert overview.quality_telemetry
    assert proposal.correction_by_indicator
    assert proposal.review_state_mix
