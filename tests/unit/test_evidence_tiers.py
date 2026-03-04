from __future__ import annotations

from alpha_app.core.evidence_registry import (
    NUMERIC_CONSTANT_EVIDENCE,
    STAGE1_SIGNALS,
    evidence_coverage,
    undocumented_numeric_constants,
)
from alpha_app.core.mock_engine import classify_stage1
from alpha_app.domain.models import CommentEvent


def _event(text: str) -> CommentEvent:
    from datetime import datetime

    return CommentEvent(
        municipality_id="thessaloniki",
        proposal_id="metro_west",
        comment_id="evidence_test",
        author_name="tester",
        comment_text=text,
        reactions={"like": 0},
        submitted_at=datetime(2026, 3, 1, 12, 0, 0),
    )


def test_all_stage1_signals_have_evidence_tier_metadata() -> None:
    result = classify_stage1(_event("Please provide clear data, I support the proposal."))
    assert set(STAGE1_SIGNALS).issubset(set(result.evidence_tier_by_signal.keys()))
    assert set(result.evidence_tier_by_signal.values()).issubset({"A", "B", "C"})


def test_no_undocumented_numeric_constants_in_registry() -> None:
    required_keys = [
        "toxicity_weight_profanity",
        "toxicity_weight_insults",
        "toxicity_weight_caps",
        "toxicity_weight_exclamation",
        "quality_weight_relevance",
        "quality_weight_evidence",
        "quality_weight_structure",
        "quality_weight_clarity",
        "quality_weight_civility",
        "quality_weight_toxicity_penalty",
        "routing_low_confidence",
        "routing_high_entropy",
        "routing_offense_gray_low",
        "routing_offense_gray_high",
    ]
    assert not undocumented_numeric_constants(required_keys=required_keys)
    assert all(NUMERIC_CONSTANT_EVIDENCE[key].owner for key in required_keys)
    assert all(NUMERIC_CONSTANT_EVIDENCE[key].updated_on for key in required_keys)


def test_evidence_coverage_reports_complete_signal_coverage() -> None:
    coverage = evidence_coverage(list(STAGE1_SIGNALS))
    assert coverage["covered_signals"] == len(STAGE1_SIGNALS)
    assert coverage["coverage_ratio"] == 1.0
