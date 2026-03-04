from __future__ import annotations

MUNICIPALITY_ID = "thessaloniki"
MUNICIPALITY_NAME = "Δήμος Θεσσαλονίκης"

INFERENCE_MODE = "mock"
JUDGE_TRIGGER_POLICY_VERSION = "v1"
FAIRNESS_POLICY_VERSION = "v1"
EVIDENCE_REGISTRY_VERSION = "v1"

REACTION_KEYS = ["like", "dislike", "love", "angry", "sad", "wow"]
LEGACY_REACTION_KEY_MAP = {
    "likes": "like",
    "support": "love",
    "laugh": "wow",
    "angry": "angry",
}
REACTION_WEIGHTS_V1 = {
    "like": 1.0,
    "love": 1.6,
    "wow": 0.8,
    "dislike": -1.1,
    "sad": -0.9,
    "angry": -1.4,
}
REACTION_PROFILE_VERSION = "v1"
MOST_RELEVANT_WEIGHTS_V1 = {
    "engagement": 0.50,
    "polarity": 0.25,
    "recency": 0.25,
}
MAX_THREAD_DEPTH = 3
FEED_PAGE_SIZE = 25

# Routing thresholds are centralized to keep evidence-tier metadata traceable.
LOW_CONFIDENCE_THRESHOLD = 0.55
HIGH_ENTROPY_THRESHOLD = 0.95
OFFENSE_GRAY_ZONE_LOW = 0.45
OFFENSE_GRAY_ZONE_HIGH = 0.65
TOXICITY_AUTOBLOCK_THRESHOLD = 0.75
TOXICITY_TARGETED_BLOCK_THRESHOLD = 0.55

REACTION_LABELS = {
    "like": "Μου αρέσει",
    "dislike": "Δεν μου αρέσει",
    "love": "Τέλειο",
    "angry": "Θυμός",
    "sad": "Λύπη",
    "wow": "Έκπληξη",
}

SERVICE_LABELS = {
    "water": "Ύδρευση",
    "electricity": "Ηλεκτρισμός",
    "traffic": "Κυκλοφορία",
    "waste": "Απορρίμματα",
    "telecom": "Τηλεπικοινωνίες",
}
STATUS_LABELS = {
    "planned": "Σχεδιασμένο",
    "active": "Ενεργό",
    "delayed": "Καθυστερημένο",
    "completed": "Ολοκληρωμένο",
}
