from __future__ import annotations

MUNICIPALITY_ID = "thessaloniki"
MUNICIPALITY_NAME = "Municipality of Thessaloniki"

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
REACTION_LABELS = {
    "like": "Like",
    "dislike": "Dislike",
    "love": "Love",
    "angry": "Angry",
    "sad": "Sad",
    "wow": "Wow",
}

SERVICE_LABELS = {
    "water": "Water",
    "electricity": "Electricity",
    "traffic": "Traffic",
    "waste": "Waste",
    "telecom": "Telecom",
}
STATUS_LABELS = {
    "planned": "Planned",
    "active": "Active",
    "delayed": "Delayed",
    "completed": "Completed",
}
