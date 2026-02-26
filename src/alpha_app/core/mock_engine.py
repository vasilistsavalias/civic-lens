from __future__ import annotations

from datetime import datetime

from alpha_app.domain.models import CommentEvent, Stage1Result

POSITIVE_WORDS = {
    "θετικό",
    "καλή",
    "καλύτερο",
    "ανθρώπινη",
    "πράσινο",
    "ισότητα",
    "επιτέλους",
    "βελτίωση",
}
NEGATIVE_WORDS = {
    "αρνητικό",
    "κακό",
    "μπλοκάρει",
    "φοβάμαι",
    "δύσκολο",
    "χωρίς",
    "καθυστέρηση",
    "πρόβλημα",
}
FOR_WORDS = {"ναι", "υπέρ", "πρέπει", "στήριξη", "συμφωνώ", "θετικό"}
AGAINST_WORDS = {"όχι", "κατά", "διαφωνώ", "μπλοκάρει", "φοβάμαι", "δύσκολο"}
IRONY_MARKERS = {"ναι καλά", "σιγά", "βέβαια", "sure", "as if"}

TOPIC_KEYWORDS = {
    "green_space": {"πράσινο", "πάρκο", "δέντρα"},
    "mobility": {"μετρό", "λεωφορεία", "κυκλοφορία", "δρόμος", "πεζοδρόμηση", "μετακίνηση"},
    "safety": {"ασφάλεια", "βράδυ", "πεζοί"},
    "economy": {"κόστος", "χρηματοδότηση", "προϋπολογισμός"},
    "parking": {"στάθμευση", "πάρκινγκ"},
}


def _normalize_text(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _bounded(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def validate_event(event: CommentEvent, known_proposal_ids: set[str]) -> None:
    if not event.comment_text.strip():
        raise ValueError("Comment text must not be empty.")
    if event.proposal_id not in known_proposal_ids:
        raise ValueError(f"Unknown proposal_id: {event.proposal_id}")
    if event.submitted_at > datetime.utcnow():
        raise ValueError("submitted_at cannot be in the future.")


def classify_stage1(event: CommentEvent) -> Stage1Result:
    text = _normalize_text(event.comment_text)
    words = set(text.replace(",", " ").replace(".", " ").replace(";", " ").split())

    pos_score = len(words & POSITIVE_WORDS)
    neg_score = len(words & NEGATIVE_WORDS)
    if pos_score > neg_score:
        sentiment = "positive"
    elif neg_score > pos_score:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    for_score = len(words & FOR_WORDS)
    against_score = len(words & AGAINST_WORDS)
    if for_score > against_score:
        stance = "for"
    elif against_score > for_score:
        stance = "against"
    else:
        stance = "neutral"

    irony_flag = any(marker in text for marker in IRONY_MARKERS)

    length_factor = _bounded(len(words) / 24.0)
    quality_bonus = 0.08 if any(token in words for token in {"αν", "εφόσον", "with", "if"}) else 0.0
    argument_quality_score = round(_bounded(0.35 + length_factor * 0.5 + quality_bonus), 2)

    certainty = 0.45 + abs(pos_score - neg_score) * 0.12 + abs(for_score - against_score) * 0.1
    confidence = round(_bounded(certainty), 2)

    tags: list[str] = []
    for topic, keys in TOPIC_KEYWORDS.items():
        if words & keys:
            tags.append(topic)

    return Stage1Result(
        comment_id=event.comment_id,
        proposal_id=event.proposal_id,
        sentiment=sentiment,
        stance=stance,
        irony_flag=irony_flag,
        argument_quality_score=argument_quality_score,
        confidence=confidence,
        tags=sorted(tags),
    )

