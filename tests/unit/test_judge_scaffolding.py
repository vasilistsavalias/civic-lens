from __future__ import annotations

from datetime import datetime

from alpha_app.core.pipeline import AlphaPipeline
from alpha_app.core.proposals import PROPOSALS


def test_hybrid_mode_invokes_judge_for_conflict_case(monkeypatch) -> None:
    monkeypatch.setattr("alpha_app.core.pipeline.INFERENCE_MODE", "hybrid")
    pipeline = AlphaPipeline(proposals=PROPOSALS, top_level_per_proposal=1, seed=2026)
    event = pipeline.submit_comment(
        "metro_west",
        "Great plan, yeah right /s. I oppose this strongly.",
        submitted_at=datetime(2026, 2, 25, 10, 0, 0),
    )
    expanded = pipeline.open_card("metro_west")
    result = next(r for r in expanded.stage1_results if r.comment_id == event.comment_id)
    assert result.judge_invoked is True
    assert result.judge_decision_id is not None
    assert "REVIEW_JUDGE_ESCALATION" in result.review_reason_codes


def test_mock_mode_keeps_judge_disabled(monkeypatch) -> None:
    monkeypatch.setattr("alpha_app.core.pipeline.INFERENCE_MODE", "mock")
    pipeline = AlphaPipeline(proposals=PROPOSALS, top_level_per_proposal=1, seed=2026)
    event = pipeline.submit_comment(
        "metro_west",
        "Please review traffic data before implementation.",
        submitted_at=datetime(2026, 2, 25, 10, 5, 0),
    )
    expanded = pipeline.open_card("metro_west")
    result = next(r for r in expanded.stage1_results if r.comment_id == event.comment_id)
    assert result.judge_invoked is False
    assert result.judge_decision_id is None
