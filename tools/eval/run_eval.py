from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import bootstrap_path  # noqa: F401
from alpha_app.core.calibration import brier_proxy, ece_proxy
from alpha_app.core.mock_engine import classify_stage1
from alpha_app.domain.models import CommentEvent


def _f1(tp: int, fp: int, fn: int) -> float:
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def _macro_f1(y_true: list[str], y_pred: list[str]) -> float:
    labels = sorted(set(y_true) | set(y_pred))
    f1s: list[float] = []
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred, strict=False) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred, strict=False) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred, strict=False) if t == label and p != label)
        f1s.append(_f1(tp, fp, fn))
    return round(sum(f1s) / max(1, len(f1s)), 4)


def _per_class_recall(y_true: list[str], y_pred: list[str]) -> dict[str, float]:
    labels = sorted(set(y_true))
    recalls: dict[str, float] = {}
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred, strict=False) if t == label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred, strict=False) if t == label and p != label)
        recalls[label] = round(tp / max(1, tp + fn), 4)
    return recalls


def _multilabel_micro_f1(y_true: list[set[str]], y_pred: list[set[str]]) -> float:
    tp = fp = fn = 0
    for truth, pred in zip(y_true, y_pred, strict=False):
        tp += len(truth & pred)
        fp += len(pred - truth)
        fn += len(truth - pred)
    return round(_f1(tp, fp, fn), 4)


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or not xs:
        return 0.0
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=False))
    den_x = math.sqrt(sum((x - mx) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - my) ** 2 for y in ys))
    if den_x == 0 or den_y == 0:
        return 0.0
    return round(num / (den_x * den_y), 4)


def _rank(values: list[float]) -> list[int]:
    unique = sorted(set(values))
    rank_map = {value: idx + 1 for idx, value in enumerate(unique)}
    return [rank_map[v] for v in values]


def _spearman(xs: list[float], ys: list[float]) -> float:
    return _pearson([float(v) for v in _rank(xs)], [float(v) for v in _rank(ys)])


def _event(sample: dict[str, object], idx: int) -> CommentEvent:
    return CommentEvent(
        municipality_id="thessaloniki",
        proposal_id=str(sample.get("proposal_id", "metro_west")),
        comment_id=f"eval_{idx:04d}",
        author_name="eval",
        comment_text=str(sample["text"]),
        reactions={"likes": 0, "support": 0, "angry": 0, "laugh": 0},
        submitted_at=__import__("datetime").datetime(2026, 3, 1, 12, 0, 0),
    )


def main() -> None:
    root = Path(__file__).resolve().parent
    public_samples = json.loads((root / "data" / "public_mapped.json").read_text(encoding="utf-8"))
    mock_samples = json.loads((root / "data" / "mock_civic_slices.json").read_text(encoding="utf-8"))
    samples = public_samples + mock_samples

    sentiment_true: list[str] = []
    sentiment_pred: list[str] = []
    stance_true: list[str] = []
    stance_pred: list[str] = []
    tox_true: list[str] = []
    tox_pred: list[str] = []
    emotion_true: list[set[str]] = []
    emotion_pred: list[set[str]] = []
    quality_true: list[float] = []
    quality_pred: list[float] = []
    calibrated_rows: list[dict[str, float]] = []
    abstain_count = 0
    slice_fp = 0
    slice_total_neg = 0

    for idx, sample in enumerate(samples):
        result = classify_stage1(_event(sample, idx))
        sentiment_true.append(str(sample["sentiment"]))
        sentiment_pred.append(result.sentiment)
        stance_true.append(str(sample["stance"]))
        stance_pred.append(result.stance)
        tox_true.append(str(sample["toxicity"]))
        tox_pred.append(str(result.agent_labels.get("toxicity", "non_toxic")))
        emotion_true.append(set(sample.get("emotions", [])))
        pred_emotions = {k for k, v in result.emotion_scores.items() if k != "neutral" and v >= 0.3}
        emotion_pred.append(pred_emotions)
        quality_true.append(float(sample.get("quality_score", 0.5)))
        quality_pred.append(float(result.argument_quality_score))
        calibrated_rows.append(result.calibrated_scores or result.agent_scores)
        if any(result.abstain_flags.values()):
            abstain_count += 1
        if sample.get("slice") == "non_offensive_criticism":
            if result.agent_labels.get("toxicity") == "toxic":
                slice_fp += 1
            slice_total_neg += 1

    merged_conf = {f"sample_{i}": row.get("sentiment", 0.5) for i, row in enumerate(calibrated_rows)}
    report = {
        "macro_f1": {
            "sentiment": _macro_f1(sentiment_true, sentiment_pred),
            "stance": _macro_f1(stance_true, stance_pred),
            "toxicity": _macro_f1(tox_true, tox_pred),
        },
        "per_class_recall": {
            "sentiment": _per_class_recall(sentiment_true, sentiment_pred),
            "stance": _per_class_recall(stance_true, stance_pred),
            "toxicity": _per_class_recall(tox_true, tox_pred),
        },
        "emotion_multilabel_f1": _multilabel_micro_f1(emotion_true, emotion_pred),
        "quality_correlation": {"pearson": _pearson(quality_true, quality_pred), "spearman": _spearman(quality_true, quality_pred)},
        "calibration": {"ece_proxy": ece_proxy(merged_conf), "brier_proxy": brier_proxy(merged_conf)},
        "abstain_rate": round(abstain_count / max(1, len(samples)), 4),
        "slice_false_positive_rate_non_offensive_criticism": round(slice_fp / max(1, slice_total_neg), 4),
        "sample_count": len(samples),
        "limitations": [
            "Public benchmark subset is mapped and reduced for mockup comparability.",
            "Calibration metrics are proxies without external ground-truth probabilities.",
            "Quality correlation uses synthetic labels in this phase.",
        ],
    }

    out_dir = Path.cwd() / "docs" / "research" / "eval_reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "latest_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# Evaluation Report (Public + Mock)",
        "",
        f"- Samples: {report['sample_count']}",
        f"- Sentiment Macro-F1: {report['macro_f1']['sentiment']}",
        f"- Stance Macro-F1: {report['macro_f1']['stance']}",
        f"- Toxicity Macro-F1: {report['macro_f1']['toxicity']}",
        f"- Emotion micro-F1: {report['emotion_multilabel_f1']}",
        f"- Quality Pearson: {report['quality_correlation']['pearson']}",
        f"- Quality Spearman: {report['quality_correlation']['spearman']}",
        f"- ECE proxy: {report['calibration']['ece_proxy']}",
        f"- Brier proxy: {report['calibration']['brier_proxy']}",
        f"- Abstain rate: {report['abstain_rate']}",
        f"- Slice FPR (non-offensive criticism): {report['slice_false_positive_rate_non_offensive_criticism']}",
        "",
        "## Limitations",
    ]
    md.extend([f"- {item}" for item in report["limitations"]])
    (out_dir / "latest_report.md").write_text("\n".join(md), encoding="utf-8")
    print("Wrote:", out_dir / "latest_report.json")
    print("Wrote:", out_dir / "latest_report.md")


if __name__ == "__main__":
    main()
