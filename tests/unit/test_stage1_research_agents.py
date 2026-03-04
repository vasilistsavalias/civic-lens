from __future__ import annotations

from datetime import datetime

from alpha_app.core.mock_engine import AGENT_NAMES, classify_stage1
from alpha_app.domain.models import CommentEvent


def _event(text: str, proposal_id: str = "metro_west") -> CommentEvent:
    return CommentEvent(
        municipality_id="thessaloniki",
        proposal_id=proposal_id,
        comment_id="c_test",
        author_name="tester",
        comment_text=text,
        reactions={"likes": 0, "support": 0, "angry": 0, "laugh": 0},
        submitted_at=datetime(2026, 3, 1, 12, 0, 0),
    )


def test_stage1_returns_ten_agent_outputs() -> None:
    result = classify_stage1(
        _event(
            "I think we should support the metro expansion because study data from 2025 shows faster mobility and less traffic."
        )
    )
    assert set(AGENT_NAMES).issubset(set(result.agent_scores.keys()))
    assert set(AGENT_NAMES).issubset(set(result.agent_labels.keys()))
    assert result.agent_labels["evidence"] in {"evidence_backed", "limited_evidence"}
    assert result.agent_labels["structure"] in {"structured", "semi_structured"}
    assert set(result.emotion_scores.keys()) == {"anger", "fear", "sadness", "joy", "trust", "disgust", "neutral"}
    assert 0.0 <= result.emotion_intensity <= 1.0


def test_profanity_and_toxicity_reduce_argument_quality() -> None:
    result = classify_stage1(_event("This is bullshit and stupid. Fuck this plan!!"))
    assert result.agent_labels["profanity"] == "contains_profanity"
    assert result.agent_labels["toxicity"] == "toxic"
    assert result.argument_quality_score <= 0.45


def test_structured_vs_unstructured_boundary() -> None:
    structured = classify_stage1(
        _event(
            "I think we should proceed, because traffic data shows delays. However, add buses first so access remains fair."
        )
    )
    unstructured = classify_stage1(_event("No. Bad idea."))

    assert structured.agent_labels["structure"] in {"structured", "semi_structured"}
    assert structured.agent_scores["structure"] > unstructured.agent_scores["structure"]
    assert unstructured.agent_labels["evidence"] == "unsupported"


def test_relevance_is_proposal_specific() -> None:
    relevant = classify_stage1(_event("Metro west needs better transport links.", proposal_id="metro_west"))
    off_topic = classify_stage1(_event("Beach nightlife is great in summer.", proposal_id="metro_west"))
    assert relevant.agent_labels["relevance"] == "relevant"
    assert off_topic.agent_labels["relevance"] == "off_topic"


def test_emotion_head_supports_bilingual_and_blended_emotions() -> None:
    result = classify_stage1(
        _event("I am afraid and worried, but also hopeful and happy for this clear proposal with evidence.")
    )
    assert result.emotion_scores["fear"] > 0.0
    assert result.emotion_scores["joy"] > 0.0
    assert result.emotion_intensity > 0.0


def test_offense_target_placeholder_is_emitted() -> None:
    targeted = classify_stage1(_event("You are stupid and this is bullshit."))
    assert targeted.offense_target in {"individual", "group", "untargeted", "unknown"}


def test_stage1_contract_v2_fields_have_valid_ranges() -> None:
    result = classify_stage1(_event("Please provide clear data and evidence; I support this proposal."))
    assert all(0.0 <= v <= 1.0 for v in result.emotion_scores.values())
    assert 0.0 <= result.emotion_intensity <= 1.0
    assert isinstance(result.calibrated_scores, dict)
    assert isinstance(result.abstain_flags, dict)
    assert isinstance(result.conflict_flags, list)
    assert isinstance(result.review_reason_codes, list)
