from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Literal

from alpha_app.domain.models import CommentEvent, Stage1Result

ReviewStatus = Literal["corrected", "unchanged", "unresolved"]
ReviewerRole = Literal["journalist", "political_scientist"]


@dataclass(frozen=True)
class CorrectionRecord:
    comment_id: str
    proposal_id: str
    indicator: str
    before_value: object
    after_value: object
    reason: str
    reviewer_role: ReviewerRole
    created_at: str


def _sentiment_score(label: str) -> float:
    if label == "positive":
        return 0.7
    if label == "negative":
        return -0.7
    return 0.0


def _bucketize(value: float) -> float:
    if value <= 0.5:
        return 0.0
    if value <= 0.8:
        return 0.6
    return 0.9


def _initial_row(comment: CommentEvent, result: Stage1Result) -> dict[str, object]:
    topic_context = result.tags[0] if result.tags else "other"
    subtopic_context = result.tags[1] if len(result.tags) > 1 else "general"
    criticism_or_agenda = "criticism" if (result.stance == "against" or result.sentiment == "negative") else "political_agenda"
    polarization_raw = round(min(1.0, abs(result.confidence - 0.5) * 2 + (0.2 if result.irony_flag else 0.0)), 2)
    populism_raw = round(min(1.0, 0.2 + (0.35 if result.stance != "neutral" else 0.0) + (0.15 if result.irony_flag else 0.0)), 2)
    return {
        "comment_id": comment.comment_id,
        "proposal_id": comment.proposal_id,
        "comment_text": comment.comment_text,
        "sentiment": result.sentiment,
        "sentiment_score": _sentiment_score(result.sentiment),
        "stance": result.stance,
        "criticism_or_agenda": criticism_or_agenda,
        "topic_context": topic_context,
        "subtopic_context": subtopic_context,
        "polarization_raw": polarization_raw,
        "populism_raw": populism_raw,
        "polarization": _bucketize(polarization_raw),
        "populism": _bucketize(populism_raw),
        "ner_limited": [],
        "argument_quality_score": result.argument_quality_score,
        "confidence": result.confidence,
        "irony_flag": result.irony_flag,
        "tags": list(result.tags),
    }


def apply_mock_reviewer_pass(
    proposal_id: str,
    comments: list[CommentEvent],
    stage1_results: list[Stage1Result],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    by_comment = {result.comment_id: result for result in stage1_results}
    initial_rows: list[dict[str, object]] = []
    final_rows: list[dict[str, object]] = []
    correction_records: list[CorrectionRecord] = []
    indicator_corrections: dict[str, int] = {k: 0 for k in ["sentiment", "criticism_or_agenda", "topic_context", "polarization", "populism"]}
    unresolved_count = 0

    review_time = datetime.utcnow()
    lag_values: list[float] = []
    for comment in comments:
        if comment.comment_id not in by_comment:
            continue
        result = by_comment[comment.comment_id]
        initial = _initial_row(comment, result)
        final = dict(initial)
        corrected = False
        unresolved = result.confidence < 0.5

        if unresolved:
            unresolved_count += 1

        if final["irony_flag"] and final["sentiment"] == "positive":
            before = final["sentiment"]
            final["sentiment"] = "neutral"
            final["sentiment_score"] = _sentiment_score("neutral")
            corrected = True
            indicator_corrections["sentiment"] += 1
            correction_records.append(
                CorrectionRecord(
                    comment_id=comment.comment_id,
                    proposal_id=proposal_id,
                    indicator="sentiment",
                    before_value=before,
                    after_value=final["sentiment"],
                    reason="Irony-aware override for optimistic sentiment.",
                    reviewer_role="journalist",
                    created_at=review_time.isoformat(timespec="seconds"),
                )
            )

        if final["criticism_or_agenda"] == "criticism" and final["sentiment"] == "positive":
            before = final["criticism_or_agenda"]
            final["criticism_or_agenda"] = "political_agenda"
            corrected = True
            indicator_corrections["criticism_or_agenda"] += 1
            correction_records.append(
                CorrectionRecord(
                    comment_id=comment.comment_id,
                    proposal_id=proposal_id,
                    indicator="criticism_or_agenda",
                    before_value=before,
                    after_value=final["criticism_or_agenda"],
                    reason="Positive sentiment reclassified as agenda emphasis.",
                    reviewer_role="journalist",
                    created_at=review_time.isoformat(timespec="seconds"),
                )
            )

        if final["topic_context"] == "other" and result.tags:
            before = final["topic_context"]
            final["topic_context"] = result.tags[0]
            corrected = True
            indicator_corrections["topic_context"] += 1
            correction_records.append(
                CorrectionRecord(
                    comment_id=comment.comment_id,
                    proposal_id=proposal_id,
                    indicator="topic_context",
                    before_value=before,
                    after_value=final["topic_context"],
                    reason="Topic fallback resolved using strongest detected tag.",
                    reviewer_role="journalist",
                    created_at=review_time.isoformat(timespec="seconds"),
                )
            )

        raw_polarization = float(final["polarization_raw"])
        bucket_polarization = _bucketize(raw_polarization)
        if float(final["polarization"]) != bucket_polarization:
            before = final["polarization"]
            final["polarization"] = bucket_polarization
            corrected = True
            indicator_corrections["polarization"] += 1
            correction_records.append(
                CorrectionRecord(
                    comment_id=comment.comment_id,
                    proposal_id=proposal_id,
                    indicator="polarization",
                    before_value=before,
                    after_value=final["polarization"],
                    reason="Value snapped to policy bucket.",
                    reviewer_role="political_scientist",
                    created_at=review_time.isoformat(timespec="seconds"),
                )
            )

        raw_populism = float(final["populism_raw"])
        bucket_populism = _bucketize(raw_populism)
        if float(final["populism"]) != bucket_populism:
            before = final["populism"]
            final["populism"] = bucket_populism
            corrected = True
            indicator_corrections["populism"] += 1
            correction_records.append(
                CorrectionRecord(
                    comment_id=comment.comment_id,
                    proposal_id=proposal_id,
                    indicator="populism",
                    before_value=before,
                    after_value=final["populism"],
                    reason="Value snapped to policy bucket.",
                    reviewer_role="political_scientist",
                    created_at=review_time.isoformat(timespec="seconds"),
                )
            )

        review_status: ReviewStatus
        if unresolved:
            review_status = "unresolved"
        elif corrected:
            review_status = "corrected"
        else:
            review_status = "unchanged"
        final["review_status"] = review_status

        lag_sec = max(0.0, (review_time - comment.submitted_at).total_seconds())
        final["review_lag_sec"] = round(lag_sec, 2)
        lag_values.append(lag_sec)

        initial_rows.append(initial)
        final_rows.append(final)

    total_items = len(final_rows)
    corrected_items = len([row for row in final_rows if row["review_status"] == "corrected"])
    unchanged_items = len([row for row in final_rows if row["review_status"] == "unchanged"])
    unresolved_items = len([row for row in final_rows if row["review_status"] == "unresolved"])
    denominator = max(1, total_items)
    indicator_rates = {k: round(v / denominator, 3) for k, v in indicator_corrections.items()}
    metrics: dict[str, object] = {
        "proposal_id": proposal_id,
        "total_items": total_items,
        "corrected_items": corrected_items,
        "unchanged_items": unchanged_items,
        "unresolved_items": unresolved_items,
        "correction_rate": round(corrected_items / denominator, 3),
        "unresolved_rate": round(unresolved_items / denominator, 3),
        "avg_review_lag_sec": round(sum(lag_values) / max(1, len(lag_values)), 2),
        "indicator_corrections": indicator_corrections,
        "indicator_rates": indicator_rates,
    }

    serialized_corrections = [asdict(record) for record in correction_records]
    return initial_rows, final_rows, serialized_corrections, metrics

