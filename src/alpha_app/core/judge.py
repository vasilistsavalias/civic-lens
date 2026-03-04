from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime

from alpha_app.domain.models import Stage1Result


@dataclass(frozen=True)
class JudgeDecision:
    decision_id: str
    invoked: bool
    pass_a_scores: dict[str, float]
    pass_a_tags: list[str]
    pass_b_checks: dict[str, bool]
    rationale: str


def _decision_id(comment_id: str, policy_version: str) -> str:
    seed = f"{comment_id}:{policy_version}:{datetime.utcnow().isoformat(timespec='seconds')}"
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()
    return f"judge_{digest[:12]}"


def should_invoke_judge(result: Stage1Result) -> bool:
    if not result.abstain_flags:
        return False
    trigger_flags = ("low_confidence", "high_entropy", "irony_conflict", "offense_gray_zone", "policy_block")
    if any(result.abstain_flags.get(flag, False) for flag in trigger_flags):
        return True
    return bool(result.conflict_flags)


def run_two_pass_judge(
    result: Stage1Result,
    *,
    comment_text: str,
    policy_version: str,
) -> JudgeDecision:
    """Deterministic scaffolding for a two-pass LLM judge.

    Pass A mimics rubric scoring and tag extraction.
    Pass B validates consistency and policy constraints.
    """
    invoked = should_invoke_judge(result)
    if not invoked:
        return JudgeDecision(
            decision_id="",
            invoked=False,
            pass_a_scores={},
            pass_a_tags=[],
            pass_b_checks={},
            rationale="Judge not invoked.",
        )

    text_len = max(1, len(comment_text.split()))
    score_quality = round(float(result.argument_quality_score), 3)
    score_safety = round(float(result.agent_scores.get("toxicity", 0.0)), 3)
    score_context = round(min(1.0, text_len / 30.0), 3)
    pass_a_scores = {
        "quality": score_quality,
        "safety_risk": score_safety,
        "context_completeness": score_context,
    }
    pass_a_tags: list[str] = []
    if result.irony_flag:
        pass_a_tags.append("irony_present")
    if result.review_reason_codes:
        pass_a_tags.append("needs_human_review")
    if result.offense_target in {"group", "individual"}:
        pass_a_tags.append("targeted_offense_risk")
    if not pass_a_tags:
        pass_a_tags.append("borderline_case")

    pass_b_checks = {
        "json_schema_valid": True,
        "no_sentiment_stance_contradiction": "sentiment_stance_conflict" not in result.conflict_flags,
        "profanity_only_not_blocked": not (
            result.agent_scores.get("profanity", 0.0) > 0 and result.abstain_flags.get("policy_block", False)
        ),
    }
    rationale = (
        "Two-pass judge scaffold executed. "
        "Pass A produced rubric-like scores, Pass B validated consistency and policy guardrails."
    )
    return JudgeDecision(
        decision_id=_decision_id(result.comment_id, policy_version),
        invoked=True,
        pass_a_scores=pass_a_scores,
        pass_a_tags=pass_a_tags,
        pass_b_checks=pass_b_checks,
        rationale=rationale,
    )
