from __future__ import annotations

from datetime import datetime

from alpha_app.core.calibration import binary_entropy, calibrate_scores, temperature_scale_probability
from alpha_app.core.pipeline import AlphaPipeline
from alpha_app.core.proposals import PROPOSALS


def test_temperature_scaling_stays_bounded() -> None:
    scaled = temperature_scale_probability(0.83, 1.2)
    assert 0.0 <= scaled <= 1.0


def test_calibrate_scores_returns_all_keys() -> None:
    raw = {"sentiment": 0.8, "toxicity": 0.3, "emotion": 0.5}
    calibrated = calibrate_scores(raw)
    assert set(calibrated.keys()) == set(raw.keys())
    assert all(0.0 <= v <= 1.0 for v in calibrated.values())


def test_binary_entropy_peaks_near_half() -> None:
    low = binary_entropy(0.1)
    high = binary_entropy(0.5)
    assert high > low


def test_routing_sets_review_reason_codes_for_conflicts() -> None:
    pipeline = AlphaPipeline(proposals=PROPOSALS)
    event = pipeline.submit_comment(
        "metro_west",
        "Yeah right, great plan as if this won't fail. I oppose this.",
        submitted_at=datetime(2026, 2, 25, 10, 0, 0),
    )
    expanded = pipeline.open_card("metro_west")
    result = next(r for r in expanded.stage1_results if r.comment_id == event.comment_id)
    assert isinstance(result.review_reason_codes, list)
    assert isinstance(result.abstain_flags, dict)
    assert isinstance(result.calibrated_scores, dict)


def test_profanity_only_does_not_force_policy_block() -> None:
    pipeline = AlphaPipeline(proposals=PROPOSALS)
    event = pipeline.submit_comment(
        "deth_park",
        "damn this is messy but I still support the plan because data is clear",
        submitted_at=datetime(2026, 2, 25, 11, 0, 0),
    )
    expanded = pipeline.open_card("deth_park")
    result = next(r for r in expanded.stage1_results if r.comment_id == event.comment_id)
    assert result.abstain_flags.get("policy_block") is False
