from __future__ import annotations

import math

DEFAULT_TEMPERATURES: dict[str, float] = {
    "sentiment": 1.2,
    "stance": 1.15,
    "emotion": 1.25,
    "irony": 1.2,
    "argument_quality": 1.1,
    "profanity": 1.05,
    "toxicity": 1.1,
    "civility": 1.15,
    "structure": 1.1,
    "evidence": 1.1,
    "relevance": 1.1,
    "clarity": 1.1,
}


def _bounded(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def temperature_scale_probability(prob: float, temperature: float) -> float:
    p = _bounded(prob, 1e-6, 1 - 1e-6)
    t = max(0.1, temperature)
    logit = math.log(p / (1.0 - p))
    scaled = 1.0 / (1.0 + math.exp(-(logit / t)))
    return round(_bounded(scaled), 4)


def calibrate_scores(raw_scores: dict[str, float], temperatures: dict[str, float] | None = None) -> dict[str, float]:
    temp_map = temperatures or DEFAULT_TEMPERATURES
    calibrated: dict[str, float] = {}
    for head, value in raw_scores.items():
        calibrated[head] = temperature_scale_probability(float(value), temp_map.get(head, 1.1))
    return calibrated


def binary_entropy(prob: float) -> float:
    p = _bounded(prob, 1e-6, 1 - 1e-6)
    return round(-(p * math.log2(p) + (1.0 - p) * math.log2(1.0 - p)), 4)


def mean_entropy(scores: dict[str, float], heads: set[str] | None = None) -> float:
    if not scores:
        return 0.0
    scoped = [v for k, v in scores.items() if heads is None or k in heads]
    if not scoped:
        return 0.0
    return round(sum(binary_entropy(v) for v in scoped) / len(scoped), 4)


def ece_proxy(scores: dict[str, float]) -> float:
    if not scores:
        return 0.0
    confidence = [max(v, 1.0 - v) for v in scores.values()]
    return round(sum((1.0 - c) for c in confidence) / len(confidence), 4)


def brier_proxy(scores: dict[str, float]) -> float:
    if not scores:
        return 0.0
    # Proxy without labels: uncertainty term p*(1-p)
    return round(sum(v * (1.0 - v) for v in scores.values()) / len(scores), 4)
