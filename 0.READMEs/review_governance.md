# Review Governance and Threshold Tuning

## Purpose
Operational runbook for abstain/review routing, threshold tuning, and drift monitoring in the mock++ phase.

## Who Should Read This
Both

## Threshold Tuning Protocol
1. Run `python tools/eval/run_eval.py` and review `docs/research/eval_reports/latest_report.md`.
2. Inspect:
   - macro-F1 by head
   - calibration proxies (ECE/Brier)
   - abstain rate
   - slice false-positive rate on non-offensive criticism
3. Tune one threshold at a time (for example `max_prob` or `offense_gray_zone`).
4. Re-run evaluation and compare deltas.
5. Accept only if:
   - slice FPR does not worsen
   - abstain rate change is justified
   - no regression in hard-case tests

## Review SLA and Escalation
- Priority `P1`: toxicity gray-zone with group/individual target markers.
- Priority `P2`: irony conflicts and high entropy.
- Priority `P3`: low confidence only.

Escalation rule:
- If unresolved review items > 25% in latest run, freeze threshold changes and perform error-analysis session.

## Metric Interpretation Guide
- `calibration_metrics`: confidence reliability proxies by head.
- `abstain_summary`: reasons for reviewer routing.
- `conflict_summary`: contradiction patterns across heads.
- `emotion_distribution`: dominant emotional tone population.

## Drift Monitoring Checklist
- Weekly:
  - compare label distributions vs previous week
  - compare abstain rate vs baseline
  - compare non-offensive criticism FPR vs baseline
- Trigger investigation when any metric shifts by >15% relative change.

## Decision Tree: Retrain vs Re-threshold
1. Are hard-case tests failing?
   - Yes -> re-threshold first if failures are boundary-related.
2. Do failures persist after two threshold iterations?
   - Yes -> plan model/lexicon update.
3. Is drift broad across multiple heads?
   - Yes -> prioritize retraining/method upgrade.
4. Is drift localized to one head with stable calibration?
   - Yes -> targeted threshold adjustment is acceptable.
