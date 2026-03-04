from __future__ import annotations

from alpha_app.core.pipeline import AlphaPipeline
from alpha_app.core.proposals import PROPOSALS


def test_architecture_metrics_cover_all_required_blocks() -> None:
    pipeline = AlphaPipeline(proposals=PROPOSALS)
    metrics = pipeline.architecture_metrics()
    required = {
        "agent_outputs",
        "agent_confidence",
        "classifier_vs_llm",
        "calibration_metrics",
        "abstain_summary",
        "conflict_summary",
        "emotion_distribution",
        "judge_reliability",
        "fairness_summary",
        "evidence_coverage",
        "api_validation",
        "queue_timeline",
        "bypass_vs_nlp",
        "store_volume",
        "store_freshness",
        "scheduler_triggers",
    }
    assert required.issubset(metrics.keys())
    for key in required:
        assert metrics[key]

