from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

EvidenceTier = Literal["A", "B", "C"]

STAGE1_SIGNALS = (
    "sentiment",
    "stance",
    "emotion",
    "irony",
    "argument_quality",
    "profanity",
    "toxicity",
    "civility",
    "structure",
    "evidence",
    "relevance",
    "clarity",
)


@dataclass(frozen=True)
class NumericConstantEvidence:
    key: str
    value: float
    tier: EvidenceTier
    rationale: str
    owner: str
    updated_on: str
    citations: tuple[str, ...]
    migration_path: str


SIGNAL_EVIDENCE_TIERS: dict[str, EvidenceTier] = {
    "sentiment": "A",
    "stance": "A",
    "emotion": "A",
    "irony": "A",
    "argument_quality": "A",
    "profanity": "C",
    "toxicity": "C",
    "civility": "A",
    "structure": "A",
    "evidence": "A",
    "relevance": "C",
    "clarity": "C",
}

SIGNAL_RATIONALE_REFS: dict[str, list[str]] = {
    "sentiment": ["semeval2017_task4"],
    "stance": ["semeval2016_task6"],
    "emotion": ["semeval2018_task1", "goemotions"],
    "irony": ["semeval2018_task3", "sarc"],
    "argument_quality": ["coling2020_argument_quality", "arxiv1909_argument_quality"],
    "profanity": ["hurtlex", "davidson2017"],
    "toxicity": ["offenseval2019", "davidson2017"],
    "civility": ["computational_politeness"],
    "structure": ["stab_gurevych_argumentation"],
    "evidence": ["wachsmuth_argument_search"],
    "relevance": ["tweet_eval"],
    "clarity": ["coling2020_argument_quality"],
}

MODEL_OR_RULE_VERSION_MOCK: dict[str, str] = {signal: "rule_v1" for signal in STAGE1_SIGNALS}
MODEL_OR_RULE_VERSION_HYBRID: dict[str, str] = {
    **{signal: "rule_v1" for signal in STAGE1_SIGNALS},
    "sentiment": "hybrid_head_v1",
    "stance": "hybrid_head_v1",
    "emotion": "hybrid_head_v1",
    "irony": "hybrid_head_v1",
    "toxicity": "hybrid_head_v1",
    "judge": "llm_judge_v1",
}

NUMERIC_CONSTANT_EVIDENCE: dict[str, NumericConstantEvidence] = {
    "toxicity_weight_profanity": NumericConstantEvidence(
        key="toxicity_weight_profanity",
        value=0.45,
        tier="C",
        rationale="Engineering prior emphasizing explicit profanity as a strong toxicity indicator.",
        owner="civic-lens-team",
        updated_on="2026-03-04",
        citations=("offenseval2019", "davidson2017"),
        migration_path="fit_on_local_labeled_toxicity_set_v2",
    ),
    "toxicity_weight_insults": NumericConstantEvidence(
        key="toxicity_weight_insults",
        value=0.35,
        tier="C",
        rationale="Engineering prior emphasizing directed insults under abuse taxonomy.",
        owner="civic-lens-team",
        updated_on="2026-03-04",
        citations=("offenseval2019", "davidson2017"),
        migration_path="fit_on_local_labeled_toxicity_set_v2",
    ),
    "toxicity_weight_caps": NumericConstantEvidence(
        key="toxicity_weight_caps",
        value=0.10,
        tier="C",
        rationale="Style-based aggression proxy used as weak additive signal.",
        owner="civic-lens-team",
        updated_on="2026-03-04",
        citations=("offenseval2019",),
        migration_path="fit_on_local_labeled_toxicity_set_v2",
    ),
    "toxicity_weight_exclamation": NumericConstantEvidence(
        key="toxicity_weight_exclamation",
        value=0.10,
        tier="C",
        rationale="Burst punctuation proxy for agitation intensity.",
        owner="civic-lens-team",
        updated_on="2026-03-04",
        citations=("offenseval2019",),
        migration_path="fit_on_local_labeled_toxicity_set_v2",
    ),
    "quality_weight_relevance": NumericConstantEvidence(
        key="quality_weight_relevance",
        value=0.30,
        tier="C",
        rationale="Domain-weighted prior to avoid highly articulate off-topic comments scoring too high.",
        owner="civic-lens-team",
        updated_on="2026-03-04",
        citations=("coling2020_argument_quality",),
        migration_path="fit_on_local_quality_annotations_v2",
    ),
    "quality_weight_evidence": NumericConstantEvidence(
        key="quality_weight_evidence",
        value=0.25,
        tier="C",
        rationale="Evidence support receives high but not dominant contribution in mock stage.",
        owner="civic-lens-team",
        updated_on="2026-03-04",
        citations=("coling2020_argument_quality", "arxiv1909_argument_quality"),
        migration_path="fit_on_local_quality_annotations_v2",
    ),
    "quality_weight_structure": NumericConstantEvidence(
        key="quality_weight_structure",
        value=0.20,
        tier="C",
        rationale="Structured argument cues improve readability and decision value.",
        owner="civic-lens-team",
        updated_on="2026-03-04",
        citations=("stab_gurevych_argumentation",),
        migration_path="fit_on_local_quality_annotations_v2",
    ),
    "quality_weight_clarity": NumericConstantEvidence(
        key="quality_weight_clarity",
        value=0.15,
        tier="C",
        rationale="Clarity is additive but secondary to evidence and relevance.",
        owner="civic-lens-team",
        updated_on="2026-03-04",
        citations=("coling2020_argument_quality",),
        migration_path="fit_on_local_quality_annotations_v2",
    ),
    "quality_weight_civility": NumericConstantEvidence(
        key="quality_weight_civility",
        value=0.10,
        tier="C",
        rationale="Civility matters for deliberation quality but should not dominate substance.",
        owner="civic-lens-team",
        updated_on="2026-03-04",
        citations=("computational_politeness",),
        migration_path="fit_on_local_quality_annotations_v2",
    ),
    "quality_weight_toxicity_penalty": NumericConstantEvidence(
        key="quality_weight_toxicity_penalty",
        value=0.15,
        tier="C",
        rationale="Penalty prevents high-quality proxy inflation on abusive text.",
        owner="civic-lens-team",
        updated_on="2026-03-04",
        citations=("offenseval2019", "davidson2017"),
        migration_path="fit_on_local_quality_annotations_v2",
    ),
    "routing_low_confidence": NumericConstantEvidence(
        key="routing_low_confidence",
        value=0.55,
        tier="C",
        rationale="Balanced default for routing uncertain predictions to review.",
        owner="civic-lens-team",
        updated_on="2026-03-04",
        citations=("guo2017_calibration",),
        migration_path="fit_on_validation_reliability_curve",
    ),
    "routing_high_entropy": NumericConstantEvidence(
        key="routing_high_entropy",
        value=0.95,
        tier="C",
        rationale="Entropy cutoff tuned for conservative uncertainty detection in mock mode.",
        owner="civic-lens-team",
        updated_on="2026-03-04",
        citations=("goemotions",),
        migration_path="fit_on_validation_uncertainty_curve",
    ),
    "routing_offense_gray_low": NumericConstantEvidence(
        key="routing_offense_gray_low",
        value=0.45,
        tier="C",
        rationale="Lower bound for borderline offense ambiguity handling.",
        owner="civic-lens-team",
        updated_on="2026-03-04",
        citations=("offenseval2019",),
        migration_path="fit_on_local_policy_decisions",
    ),
    "routing_offense_gray_high": NumericConstantEvidence(
        key="routing_offense_gray_high",
        value=0.65,
        tier="C",
        rationale="Upper bound for borderline offense ambiguity handling.",
        owner="civic-lens-team",
        updated_on="2026-03-04",
        citations=("offenseval2019",),
        migration_path="fit_on_local_policy_decisions",
    ),
}


def default_evidence_tier_by_signal() -> dict[str, EvidenceTier]:
    return dict(SIGNAL_EVIDENCE_TIERS)


def default_signal_rationale_refs() -> dict[str, list[str]]:
    return {signal: list(refs) for signal, refs in SIGNAL_RATIONALE_REFS.items()}


def model_or_rule_versions(inference_mode: str) -> dict[str, str]:
    if inference_mode == "hybrid":
        return dict(MODEL_OR_RULE_VERSION_HYBRID)
    return dict(MODEL_OR_RULE_VERSION_MOCK)


def evidence_coverage(signals: list[str]) -> dict[str, object]:
    total = max(1, len(signals))
    tier_counts = {"A": 0, "B": 0, "C": 0}
    covered = 0
    for signal in signals:
        tier = SIGNAL_EVIDENCE_TIERS.get(signal)
        if tier:
            covered += 1
            tier_counts[tier] += 1
    return {
        "updated_on": date.today().isoformat(),
        "covered_signals": covered,
        "total_signals": len(signals),
        "coverage_ratio": round(covered / total, 4),
        "tier_counts": tier_counts,
        "tier_ratios": {k: round(v / total, 4) for k, v in tier_counts.items()},
    }


def undocumented_numeric_constants(required_keys: list[str] | None = None) -> list[str]:
    keys = required_keys or list(NUMERIC_CONSTANT_EVIDENCE.keys())
    return [key for key in keys if key not in NUMERIC_CONSTANT_EVIDENCE]
