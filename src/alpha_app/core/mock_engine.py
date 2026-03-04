from __future__ import annotations

import re
import unicodedata
from datetime import datetime

from alpha_app.config import INFERENCE_MODE, MAX_THREAD_DEPTH
from alpha_app.core.evidence_registry import (
    NUMERIC_CONSTANT_EVIDENCE,
    default_evidence_tier_by_signal,
    default_signal_rationale_refs,
    model_or_rule_versions,
)
from alpha_app.domain.models import CommentEvent, Stage1Result

# Research-backed mock agent catalog used in Stage-1.
AGENT_NAMES = (
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
)

POSITIVE_WORDS = {
    "\u03b8\u03b5\u03c4\u03b9\u03ba\u03bf",
    "\u03ba\u03b1\u03bb\u03b7",
    "\u03ba\u03b1\u03bb\u03c5\u03c4\u03b5\u03c1\u03bf",
    "\u03b1\u03bd\u03b8\u03c1\u03c9\u03c0\u03b9\u03bd\u03b7",
    "\u03c0\u03c1\u03b1\u03c3\u03b9\u03bd\u03bf",
    "\u03b9\u03c3\u03bf\u03c4\u03b7\u03c4\u03b1",
    "\u03b5\u03c0\u03b9\u03c4\u03b5\u03bb\u03bf\u03c5\u03c2",
    "\u03b2\u03b5\u03bb\u03c4\u03b9\u03c9\u03c3\u03b7",
    "\u03c3\u03c5\u03bc\u03c6\u03c9\u03bd\u03c9",
    "\u03bd\u03b1\u03b9",
    "good",
    "great",
    "support",
    "agree",
}
NEGATIVE_WORDS = {
    "\u03b1\u03c1\u03bd\u03b7\u03c4\u03b9\u03ba\u03bf",
    "\u03ba\u03b1\u03ba\u03bf",
    "\u03bc\u03c0\u03bb\u03bf\u03ba\u03b1\u03c1\u03b5\u03b9",
    "\u03c6\u03bf\u03b2\u03b1\u03bc\u03b1\u03b9",
    "\u03b4\u03c5\u03c3\u03ba\u03bf\u03bb\u03bf",
    "\u03c7\u03c9\u03c1\u03b9\u03c2",
    "\u03ba\u03b1\u03b8\u03c5\u03c3\u03c4\u03b5\u03c1\u03b7\u03c3\u03b7",
    "\u03c0\u03c1\u03bf\u03b2\u03bb\u03b7\u03bc\u03b1",
    "bad",
    "worse",
    "fail",
    "problem",
}
FOR_WORDS = {
    "\u03bd\u03b1\u03b9",
    "\u03c5\u03c0\u03b5\u03c1",
    "\u03c0\u03c1\u03b5\u03c0\u03b5\u03b9",
    "\u03c3\u03c4\u03b7\u03c1\u03b9\u03be\u03b7",
    "\u03c3\u03c5\u03bc\u03c6\u03c9\u03bd\u03c9",
    "support",
    "agree",
}
AGAINST_WORDS = {
    "\u03bf\u03c7\u03b9",
    "\u03ba\u03b1\u03c4\u03b1",
    "\u03b4\u03b9\u03b1\u03c6\u03c9\u03bd\u03c9",
    "\u03bc\u03c0\u03bb\u03bf\u03ba\u03b1\u03c1\u03b5\u03b9",
    "\u03c6\u03bf\u03b2\u03b1\u03bc\u03b1\u03b9",
    "against",
    "oppose",
}

IRONY_MARKERS = {
    "\u03bd\u03b1\u03b9 \u03ba\u03b1\u03bb\u03b1",
    "\u03c3\u03b9\u03b3\u03b1",
    "\u03b2\u03b5\u03b2\u03b1\u03b9\u03b1",
    "as if",
    "yeah right",
    "/s",
}

PROFANITY_WORDS = {
    "fuck",
    "fucking",
    "shit",
    "bullshit",
    "damn",
    "crap",
    "\u03bc\u03b1\u03bb\u03b1\u03ba\u03b1\u03c2",
    "\u03bc\u03b1\u03bb\u03b1\u03ba\u03b9\u03b1",
    "\u03c3\u03ba\u03b1\u03c4\u03b1",
    "\u03b3\u03b1\u03bc\u03c9",
}
INSULT_WORDS = {
    "idiot",
    "stupid",
    "moron",
    "\u03b2\u03bb\u03b1\u03ba\u03b1\u03c2",
    "\u03b7\u03bb\u03b9\u03b8\u03b9\u03bf\u03c2",
    "\u03b1\u03c7\u03c1\u03b7\u03c3\u03c4\u03bf\u03c2",
}
POLITENESS_WORDS = {
    "please",
    "thanks",
    "thank",
    "\u03c0\u03b1\u03c1\u03b1\u03ba\u03b1\u03bb\u03c9",
    "\u03b5\u03c5\u03c7\u03b1\u03c1\u03b9\u03c3\u03c4\u03c9",
    "\u03bc\u03b5 \u03c3\u03b5\u03b2\u03b1\u03c3\u03bc\u03bf",
}
CLAIM_MARKERS = {
    "\u03c0\u03b9\u03c3\u03c4\u03b5\u03c5\u03c9",
    "\u03b8\u03b5\u03c9\u03c1\u03c9",
    "\u03c0\u03c1\u03bf\u03c4\u03b5\u03b9\u03bd\u03c9",
    "\u03c0\u03c1\u03b5\u03c0\u03b5\u03b9",
    "i think",
    "we should",
}
REASON_MARKERS = {
    "\u03b5\u03c0\u03b5\u03b9\u03b4\u03b7",
    "\u03b4\u03b9\u03bf\u03c4\u03b9",
    "\u03bb\u03bf\u03b3\u03c9",
    "\u03b1\u03bd",
    "\u03b5\u03c6\u03bf\u03c3\u03bf\u03bd",
    "because",
    "since",
    "if",
    "therefore",
}
COUNTERARG_MARKERS = {
    "\u03bf\u03bc\u03c9\u03c2",
    "\u03b1\u03bb\u03bb\u03b1",
    "\u03c0\u03b1\u03c1\u03bf\u03bb\u03b1",
    "however",
    "but",
}
SOURCE_MARKERS = {"http", "www", "source", "study", "report", "data", "\u03c0\u03b7\u03b3\u03b7", "\u03bc\u03b5\u03bb\u03b5\u03c4\u03b7"}
CLARITY_MARKERS = {
    "\u03c3\u03b1\u03c6\u03b7",
    "\u03c3\u03c5\u03b3\u03ba\u03b5\u03ba\u03c1\u03b9\u03bc\u03b5\u03bd\u03b1",
    "\u03c0\u03c1\u03bf\u03c4\u03b1\u03c3\u03b7",
    "clear",
    "specifically",
    "concretely",
}
OFFENSE_TARGET_GROUP_MARKERS = {"immigrants", "foreigners", "muslims", "women", "men", "\u03bc\u03b5\u03c4\u03b1\u03bd\u03b1\u03c3\u03c4\u03b5\u03c2"}
OFFENSE_TARGET_INDIVIDUAL_MARKERS = {"you", "he", "she", "\u03b5\u03c3\u03c5", "\u03b1\u03c5\u03c4\u03bf\u03c2", "\u03b1\u03c5\u03c4\u03b7"}

EMOTION_KEYWORDS = {
    "anger": {"\u03bf\u03c1\u03b3\u03b7", "\u03b8\u03c5\u03bc\u03cc\u03c2", "angry", "furious", "rage"},
    "fear": {"\u03c6\u03bf\u03b2\u03bf\u03c2", "\u03c6\u03bf\u03b2\u03b1\u03bc\u03b1\u03b9", "fear", "afraid", "worry"},
    "sadness": {"\u03bb\u03c5\u03c0\u03b7", "\u03c3\u03c4\u03b5\u03bd\u03b1\u03c7\u03c9\u03c1\u03b9\u03b1", "sad", "disappointed", "upset"},
    "joy": {"\u03c7\u03b1\u03c1\u03b1", "\u03c7\u03b1\u03b9\u03c1\u03bf\u03bc\u03b1\u03b9", "happy", "great", "excellent"},
    "trust": {"\u03b5\u03bc\u03c0\u03b9\u03c3\u03c4\u03bf\u03c3\u03c5\u03bd\u03b7", "\u03b5\u03bc\u03c0\u03b9\u03c3\u03c4\u03b5\u03c5\u03bf\u03bc\u03b1\u03b9", "trust", "reliable"},
    "disgust": {"\u03b1\u03b7\u03b4\u03b9\u03b1", "\u03b1\u03c0\u03b5\u03c7\u03b8\u03b1\u03bd\u03bf\u03bc\u03b1\u03b9", "disgusting", "gross"},
}

TOPIC_KEYWORDS = {
    "green_space": {
        "\u03c0\u03c1\u03b1\u03c3\u03b9\u03bd\u03bf",
        "\u03c0\u03b1\u03c1\u03ba\u03bf",
        "\u03b4\u03b5\u03bd\u03c4\u03c1\u03b1",
        "park",
        "green",
    },
    "mobility": {
        "\u03bc\u03b5\u03c4\u03c1\u03bf",
        "\u03bb\u03b5\u03c9\u03c6\u03bf\u03c1\u03b5\u03b9\u03b1",
        "\u03ba\u03c5\u03ba\u03bb\u03bf\u03c6\u03bf\u03c1\u03b9\u03b1",
        "\u03b4\u03c1\u03bf\u03bc\u03bf\u03c2",
        "\u03c0\u03b5\u03b6\u03bf\u03b4\u03c1\u03bf\u03bc\u03b7\u03c3\u03b7",
        "traffic",
        "transport",
        "metro",
    },
    "safety": {"\u03b1\u03c3\u03c6\u03b1\u03bb\u03b5\u03b9\u03b1", "\u03c0\u03b5\u03b6\u03bf\u03b9", "safety"},
    "economy": {
        "\u03ba\u03bf\u03c3\u03c4\u03bf\u03c2",
        "\u03c7\u03c1\u03b7\u03bc\u03b1\u03c4\u03bf\u03b4\u03bf\u03c4\u03b7\u03c3\u03b7",
        "\u03c0\u03c1\u03bf\u03cb\u03c0\u03bf\u03bb\u03bf\u03b3\u03b9\u03c3\u03bc\u03bf\u03c2",
        "budget",
        "cost",
    },
    "parking": {"\u03c3\u03c4\u03b1\u03b8\u03bc\u03b5\u03c5\u03c3\u03b7", "\u03c0\u03b1\u03c1\u03ba\u03b9\u03bd\u03b3\u03ba", "parking"},
}
PROPOSAL_KEYWORDS = {
    "deth_park": {"\u03b4\u03b5\u03b8", "\u03c0\u03b1\u03c1\u03ba\u03bf", "\u03c0\u03c1\u03b1\u03c3\u03b9\u03bd\u03bf", "park"},
    "nikis_pedestrian": {
        "\u03bd\u03b9\u03ba\u03b7\u03c2",
        "\u03c0\u03b5\u03b6\u03bf\u03b4\u03c1\u03bf\u03bc\u03b7\u03c3\u03b7",
        "\u03c0\u03b1\u03c1\u03b1\u03bb\u03b9\u03b1",
        "pedestrian",
        "coastal",
    },
    "metro_west": {"\u03bc\u03b5\u03c4\u03c1\u03bf", "\u03b4\u03c5\u03c4\u03b9\u03ba\u03b1", "metro", "west"},
}

TOKEN_SPLIT_RE = re.compile(r"[^\w]+", flags=re.UNICODE)

TOXICITY_WEIGHT_PROFANITY = float(NUMERIC_CONSTANT_EVIDENCE["toxicity_weight_profanity"].value)
TOXICITY_WEIGHT_INSULTS = float(NUMERIC_CONSTANT_EVIDENCE["toxicity_weight_insults"].value)
TOXICITY_WEIGHT_CAPS = float(NUMERIC_CONSTANT_EVIDENCE["toxicity_weight_caps"].value)
TOXICITY_WEIGHT_EXCLAMATION = float(NUMERIC_CONSTANT_EVIDENCE["toxicity_weight_exclamation"].value)

QUALITY_WEIGHT_RELEVANCE = float(NUMERIC_CONSTANT_EVIDENCE["quality_weight_relevance"].value)
QUALITY_WEIGHT_EVIDENCE = float(NUMERIC_CONSTANT_EVIDENCE["quality_weight_evidence"].value)
QUALITY_WEIGHT_STRUCTURE = float(NUMERIC_CONSTANT_EVIDENCE["quality_weight_structure"].value)
QUALITY_WEIGHT_CLARITY = float(NUMERIC_CONSTANT_EVIDENCE["quality_weight_clarity"].value)
QUALITY_WEIGHT_CIVILITY = float(NUMERIC_CONSTANT_EVIDENCE["quality_weight_civility"].value)
QUALITY_WEIGHT_TOXICITY_PENALTY = float(NUMERIC_CONSTANT_EVIDENCE["quality_weight_toxicity_penalty"].value)


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def _normalize_text(text: str) -> str:
    lowered = _strip_accents(text.strip().lower())
    return " ".join(lowered.split())


def _tokenize(normalized_text: str) -> list[str]:
    return [tok for tok in TOKEN_SPLIT_RE.split(normalized_text) if tok]


def _bounded(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _contains_any_phrase(text: str, phrases: set[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def _caps_ratio(raw_text: str) -> float:
    letters = [ch for ch in raw_text if ch.isalpha()]
    if not letters:
        return 0.0
    uppercase = [ch for ch in letters if ch.isupper()]
    return len(uppercase) / len(letters)


def _language_slice_key(text: str) -> str:
    letters = [ch for ch in text if ch.isalpha()]
    if not letters:
        return "lang:unknown"
    greek_letters = sum(1 for ch in letters if "\u0370" <= ch <= "\u03FF" or "\u1F00" <= ch <= "\u1FFF")
    latin_letters = sum(1 for ch in letters if ("A" <= ch <= "Z") or ("a" <= ch <= "z"))
    if greek_letters and latin_letters:
        return "lang:mixed"
    if greek_letters:
        return "lang:el"
    if latin_letters:
        return "lang:en"
    return "lang:other"


def validate_event(event: CommentEvent, known_proposal_ids: set[str]) -> None:
    if not event.comment_text.strip():
        raise ValueError("Comment text must not be empty.")
    if event.proposal_id not in known_proposal_ids:
        raise ValueError(f"Unknown proposal_id: {event.proposal_id}")
    if event.submitted_at > datetime.utcnow():
        raise ValueError("submitted_at cannot be in the future.")
    if event.thread_depth < 0:
        raise ValueError("thread_depth cannot be negative.")
    if event.thread_depth > MAX_THREAD_DEPTH:
        raise ValueError(f"thread_depth exceeds MAX_THREAD_DEPTH={MAX_THREAD_DEPTH}.")
    if event.parent_comment_id is None and event.thread_depth != 0:
        raise ValueError("Top-level comments must have thread_depth=0.")


def classify_stage1(event: CommentEvent) -> Stage1Result:
    normalized = _normalize_text(event.comment_text)
    words = set(_tokenize(normalized))
    raw_text = event.comment_text

    pos_score = len(words & POSITIVE_WORDS)
    neg_score = len(words & NEGATIVE_WORDS)
    if pos_score > neg_score:
        sentiment = "positive"
    elif neg_score > pos_score:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    sentiment_scalar = {"positive": 1.0, "neutral": 0.5, "negative": 0.0}[sentiment]

    for_score = len(words & FOR_WORDS)
    against_score = len(words & AGAINST_WORDS)
    if for_score > against_score:
        stance = "for"
    elif against_score > for_score:
        stance = "against"
    else:
        stance = "neutral"
    stance_scalar = {"for": 1.0, "neutral": 0.5, "against": 0.0}[stance]

    # Deterministic multi-label emotion head with normalized intensity.
    emotion_scores = {label: 0.0 for label in ("anger", "fear", "sadness", "joy", "trust", "disgust", "neutral")}
    emotion_hits: dict[str, int] = {}
    for emotion, keys in EMOTION_KEYWORDS.items():
        hits = len(words & keys)
        emotion_hits[emotion] = hits
    total_emotion_hits = sum(emotion_hits.values())
    if total_emotion_hits > 0:
        for emotion, hits in emotion_hits.items():
            emotion_scores[emotion] = round(_bounded(hits / max(1, total_emotion_hits)), 2)
        emotion_scores["neutral"] = round(_bounded(1.0 - sum(v for k, v in emotion_scores.items() if k != "neutral")), 2)
    else:
        emotion_scores["neutral"] = 1.0
    emotion_intensity = round(_bounded(total_emotion_hits / 4.0), 2)
    dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]

    irony_flag = _contains_any_phrase(normalized, IRONY_MARKERS)
    irony_score = 1.0 if irony_flag else 0.0

    profanity_hits = len(words & PROFANITY_WORDS)
    profanity_score = _bounded(profanity_hits / 2.0)
    profanity_label = "contains_profanity" if profanity_hits > 0 else "clean"

    insult_hits = len(words & INSULT_WORDS)
    caps = _caps_ratio(raw_text)
    exclamatory = 1.0 if raw_text.count("!") >= 2 else 0.0
    toxicity_score = _bounded(
        TOXICITY_WEIGHT_PROFANITY * profanity_score
        + TOXICITY_WEIGHT_INSULTS * _bounded(insult_hits / 2.0)
        + TOXICITY_WEIGHT_CAPS * caps
        + TOXICITY_WEIGHT_EXCLAMATION * exclamatory
    )
    toxicity_label = "toxic" if toxicity_score >= 0.45 else "non_toxic"

    politeness_hits = len(words & POLITENESS_WORDS)
    civility_score = _bounded(0.6 * (1.0 - toxicity_score) + 0.4 * _bounded(politeness_hits / 2.0))
    if civility_score >= 0.65:
        civility_label = "civil"
    elif civility_score >= 0.4:
        civility_label = "mixed"
    else:
        civility_label = "uncivil"

    reason_hits = len(words & REASON_MARKERS)
    source_hits = len(words & SOURCE_MARKERS)
    clarity_hits = len(words & CLARITY_MARKERS)
    numeric_signal = 1.0 if any(ch.isdigit() for ch in raw_text) else 0.0
    evidence_score = _bounded(0.45 * _bounded(reason_hits / 2.0) + 0.35 * _bounded(source_hits / 2.0) + 0.2 * numeric_signal)
    if evidence_score >= 0.6:
        evidence_label = "evidence_backed"
    elif evidence_score >= 0.3:
        evidence_label = "limited_evidence"
    else:
        evidence_label = "unsupported"

    claim_signal = 1.0 if _contains_any_phrase(normalized, CLAIM_MARKERS) else 0.0
    reason_signal = 1.0 if reason_hits > 0 else 0.0
    counter_signal = 1.0 if _contains_any_phrase(normalized, COUNTERARG_MARKERS) else 0.0
    length_signal = 1.0 if len(words) >= 12 else 0.0
    structure_score = round(_bounded((claim_signal + reason_signal + counter_signal + length_signal) / 4.0), 2)
    if structure_score >= 0.75:
        structure_label = "structured"
    elif structure_score >= 0.5:
        structure_label = "semi_structured"
    else:
        structure_label = "unstructured"

    proposal_terms = PROPOSAL_KEYWORDS.get(event.proposal_id, set())
    general_topic_terms = set().union(*TOPIC_KEYWORDS.values())
    relevance_hits = len(words & (proposal_terms | general_topic_terms))
    if relevance_hits >= 2:
        relevance_score = 1.0
    elif relevance_hits == 1:
        relevance_score = 0.6
    else:
        relevance_score = 0.0
    relevance_label = "relevant" if relevance_score >= 0.6 else "off_topic"

    clarity_score = _bounded(0.5 * _bounded(clarity_hits / 2.0) + 0.5 * _bounded(len(words) / 20.0))

    argument_quality_score = round(
        _bounded(
            QUALITY_WEIGHT_RELEVANCE * relevance_score
            + QUALITY_WEIGHT_EVIDENCE * evidence_score
            + QUALITY_WEIGHT_STRUCTURE * structure_score
            + QUALITY_WEIGHT_CLARITY * clarity_score
            + QUALITY_WEIGHT_CIVILITY * civility_score
            - QUALITY_WEIGHT_TOXICITY_PENALTY * toxicity_score
        ),
        2,
    )
    if argument_quality_score >= 0.7:
        argument_quality_label = "high"
    elif argument_quality_score >= 0.45:
        argument_quality_label = "medium"
    else:
        argument_quality_label = "low"

    certainty = 0.35 + min(0.25, abs(pos_score - neg_score) * 0.12) + min(0.2, abs(for_score - against_score) * 0.1) + 0.2 * structure_score
    confidence = round(_bounded(certainty), 2)

    offense_target = "unknown"
    if toxicity_score >= 0.45 or profanity_hits > 0:
        if words & OFFENSE_TARGET_GROUP_MARKERS:
            offense_target = "group"
        elif words & OFFENSE_TARGET_INDIVIDUAL_MARKERS:
            offense_target = "individual"
        else:
            offense_target = "untargeted"

    tags: list[str] = []
    for topic, keys in TOPIC_KEYWORDS.items():
        if words & keys:
            tags.append(topic)
    fairness_slice_keys = sorted({_language_slice_key(raw_text), f"offense_target:{offense_target}"})

    agent_scores = {
        "sentiment": round(sentiment_scalar, 2),
        "stance": round(stance_scalar, 2),
        "emotion": round(max(v for k, v in emotion_scores.items() if k != "neutral"), 2),
        "irony": round(irony_score, 2),
        "argument_quality": round(argument_quality_score, 2),
        "profanity": round(profanity_score, 2),
        "toxicity": round(toxicity_score, 2),
        "civility": round(civility_score, 2),
        "structure": round(structure_score, 2),
        "evidence": round(evidence_score, 2),
        "relevance": round(relevance_score, 2),
        "clarity": round(clarity_score, 2),
    }
    agent_labels = {
        "sentiment": sentiment,
        "stance": stance,
        "emotion": dominant_emotion,
        "irony": "ironic" if irony_flag else "non_ironic",
        "argument_quality": argument_quality_label,
        "profanity": profanity_label,
        "toxicity": toxicity_label,
        "civility": civility_label,
        "structure": structure_label,
        "evidence": evidence_label,
        "relevance": relevance_label,
        "clarity": "clear" if clarity_score >= 0.6 else "unclear",
    }

    return Stage1Result(
        comment_id=event.comment_id,
        proposal_id=event.proposal_id,
        sentiment=sentiment,
        stance=stance,
        irony_flag=irony_flag,
        argument_quality_score=argument_quality_score,
        confidence=confidence,
        tags=sorted(tags),
        agent_scores=agent_scores,
        agent_labels=agent_labels,
        emotion_scores=emotion_scores,
        emotion_intensity=emotion_intensity,
        offense_target=offense_target,  # type: ignore[arg-type]
        evidence_tier_by_signal=default_evidence_tier_by_signal(),
        signal_rationale_refs=default_signal_rationale_refs(),
        model_or_rule_version=model_or_rule_versions(INFERENCE_MODE),
        fairness_slice_keys=fairness_slice_keys,
    )
