from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import bootstrap_path  # noqa: F401
import alpha_app.core.pipeline as pipeline_module
from alpha_app.core.calibration import brier_proxy, ece_proxy
from alpha_app.core.evidence_registry import STAGE1_SIGNALS, evidence_coverage
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
        reactions={"like": 0, "love": 0, "angry": 0, "wow": 0, "sad": 0, "dislike": 0},
        submitted_at=__import__("datetime").datetime(2026, 3, 1, 12, 0, 0),
    )


def _binary_rates(y_true: list[str], y_pred: list[str], positive_label: str = "toxic") -> dict[str, float]:
    tp = sum(1 for t, p in zip(y_true, y_pred, strict=False) if t == positive_label and p == positive_label)
    tn = sum(1 for t, p in zip(y_true, y_pred, strict=False) if t != positive_label and p != positive_label)
    fp = sum(1 for t, p in zip(y_true, y_pred, strict=False) if t != positive_label and p == positive_label)
    fn = sum(1 for t, p in zip(y_true, y_pred, strict=False) if t == positive_label and p != positive_label)
    fpr = fp / max(1, fp + tn)
    fnr = fn / max(1, fn + tp)
    tpr = tp / max(1, tp + fn)
    auc_proxy = 0.5 * ((tp / max(1, tp + fn)) + (tn / max(1, tn + fp)))
    return {
        "fpr": round(fpr, 4),
        "fnr": round(fnr, 4),
        "tpr": round(tpr, 4),
        "auc_proxy": round(auc_proxy, 4),
        "count": len(y_true),
    }


def _fairness_report(
    slice_keys_by_sample: list[list[str]],
    tox_true: list[str],
    tox_pred: list[str],
) -> dict[str, object]:
    grouped: dict[str, dict[str, list[str]]] = {}
    for keys, truth, pred in zip(slice_keys_by_sample, tox_true, tox_pred, strict=False):
        for key in keys:
            grouped.setdefault(key, {"true": [], "pred": []})
            grouped[key]["true"].append(truth)
            grouped[key]["pred"].append(pred)

    slice_metrics: dict[str, dict[str, float]] = {}
    for key, vals in grouped.items():
        slice_metrics[key] = _binary_rates(vals["true"], vals["pred"])

    if not slice_metrics:
        return {
            "slice_metrics": {},
            "gap_summary": {"fpr_gap": 0.0, "fnr_gap": 0.0, "tpr_gap": 0.0, "auc_gap": 0.0},
            "language_gap": {"el_vs_en_fpr_gap": 0.0, "el_vs_en_fnr_gap": 0.0},
        }

    def _gap(metric: str) -> float:
        values = [m[metric] for m in slice_metrics.values()]
        return round(max(values) - min(values), 4)

    lang_el = slice_metrics.get("lang:el")
    lang_en = slice_metrics.get("lang:en")
    language_gap = {
        "el_vs_en_fpr_gap": round(abs((lang_el or {}).get("fpr", 0.0) - (lang_en or {}).get("fpr", 0.0)), 4),
        "el_vs_en_fnr_gap": round(abs((lang_el or {}).get("fnr", 0.0) - (lang_en or {}).get("fnr", 0.0)), 4),
    }

    return {
        "slice_metrics": slice_metrics,
        "gap_summary": {
            "fpr_gap": _gap("fpr"),
            "fnr_gap": _gap("fnr"),
            "tpr_gap": _gap("tpr"),
            "auc_gap": _gap("auc_proxy"),
        },
        "language_gap": language_gap,
    }


def _judge_reliability(results: list[object]) -> dict[str, float]:
    invoked = [r for r in results if bool(getattr(r, "judge_invoked", False))]
    if not results:
        return {
            "judge_invocation_rate": 0.0,
            "decision_id_completeness": 0.0,
            "judge_human_agreement_proxy": 0.0,
            "inter_judge_consistency_proxy": 1.0,
        }

    id_complete = [r for r in invoked if getattr(r, "judge_decision_id", None)]
    agreement_proxy = [
        r
        for r in invoked
        if ("REVIEW_JUDGE_ESCALATION" in getattr(r, "review_reason_codes", []))
        == bool(getattr(r, "judge_invoked", False))
    ]
    return {
        "judge_invocation_rate": round(len(invoked) / max(1, len(results)), 4),
        "decision_id_completeness": round(len(id_complete) / max(1, len(invoked)), 4),
        "judge_human_agreement_proxy": round(len(agreement_proxy) / max(1, len(invoked)), 4),
        "inter_judge_consistency_proxy": 1.0,
    }


def main() -> None:
    root = Path(__file__).resolve().parent
    public_samples = json.loads((root / "data" / "public_mapped.json").read_text(encoding="utf-8"))
    mock_samples = json.loads((root / "data" / "mock_civic_slices.json").read_text(encoding="utf-8"))
    samples = public_samples + mock_samples

    # Eval runs in hybrid mode to validate judge scaffolding and fairness routing blocks.
    pipeline_module.INFERENCE_MODE = "hybrid"
    pipeline = pipeline_module.AlphaPipeline(top_level_per_proposal=1, seed=2026)

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
    slice_keys_by_sample: list[list[str]] = []
    results: list[object] = []

    for idx, sample in enumerate(samples):
        result = pipeline.analyze_event(_event(sample, idx))
        results.append(result)
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
        slice_keys_by_sample.append(list(result.fairness_slice_keys))
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
        "quality_correlation": {
            "pearson": _pearson(quality_true, quality_pred),
            "spearman": _spearman(quality_true, quality_pred),
        },
        "calibration": {
            "ece_proxy": ece_proxy(merged_conf),
            "brier_proxy": brier_proxy(merged_conf),
        },
        "abstain_rate": round(abstain_count / max(1, len(samples)), 4),
        "slice_false_positive_rate_non_offensive_criticism": round(slice_fp / max(1, slice_total_neg), 4),
        "fairness": _fairness_report(slice_keys_by_sample, tox_true, tox_pred),
        "judge_reliability": _judge_reliability(results),
        "evidence_coverage": evidence_coverage(list(STAGE1_SIGNALS)),
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
        f"- Fairness FPR gap: {report['fairness']['gap_summary']['fpr_gap']}",
        f"- Judge invocation rate: {report['judge_reliability']['judge_invocation_rate']}",
        f"- Evidence coverage ratio: {report['evidence_coverage']['coverage_ratio']}",
        "",
        "## Limitations",
    ]
    md.extend([f"- {item}" for item in report["limitations"]])
    (out_dir / "latest_report.md").write_text("\n".join(md), encoding="utf-8")
    print("Wrote:", out_dir / "latest_report.json")
    print("Wrote:", out_dir / "latest_report.md")


if __name__ == "__main__":
    main()
