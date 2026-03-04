# Civic Lens Final System Spec (Mock++ to Hybrid)

## Purpose
Decision-complete product specification that separates:
- current mock behavior,
- target hybrid behavior,
- governance/evidence/fairness requirements.

## Current Mock++ Behavior
1. Deterministic lexical multi-head scoring.
2. Per-comment outputs: sentiment, stance, emotion, irony, quality, safety split.
3. Calibration transform + abstain/review routing.
4. Artifact and telemetry outputs for review/audit.

## Final Hybrid Behavior
1. Heuristic gate computes fast priors and guardrails.
2. Task-specific model heads produce probabilities and labels.
3. Calibration and uncertainty module normalizes confidence.
4. Two-pass constrained LLM judge handles only uncertain/conflicted/borderline cases.
5. Human review remains final authority for high-risk items.
6. Fairness auditor reports slice gaps each run.

## Per-Agent Role / Classifier / Metric
1. Heuristic Gate: normalization/feature precompute; latency and fallback coverage.
2. Sentiment: 3-way classifier; Macro-F1 + per-class recall.
3. Stance: target-aware classifier; Macro-F1 + per-class recall.
4. Emotion: multi-label classifier; micro-F1.
5. Irony: binary classifier; F1 and conflict-trigger precision.
6. Profanity: lexical/model detector; precision@policy threshold.
7. Toxicity: offense classifier; Macro-F1 + slice FPR.
8. Civility: civility/politeness classifier; F1 + calibration.
9. Structure: argument structure classifier; agreement with rubric labels.
10. Evidence: evidence-support classifier; correlation with human rubric.
11. Relevance: topic relevance classifier; F1 + off-topic false positive rate.
12. Calibration/Uncertainty: confidence normalization; ECE/Brier.
13. LLM Adjudication: two-pass rubric judge; invocation rate + agreement proxy.
14. Fairness Auditor: slice gap analyzer; FPR/FNR/TPR/AUC gaps.

## Evidence Tier Registry
Numerics and claims must be declared in:
- `src/alpha_app/core/evidence_registry.py`

Every decision-critical constant must include:
1. `tier`
2. `rationale`
3. `owner`
4. `updated_on`
5. `citations`
6. `migration_path`

## Fairness Governance
Minimum required reports per release:
1. Language slice gaps (`lang:el`, `lang:en`, `lang:mixed`).
2. Offense target slices (`individual`, `group`, `untargeted`, `unknown`).
3. Counterfactual template suite for sensitive substitutions.
4. Reviewer-facing summary with observed gaps and action items.

## Review Policy
1. Auto-action only when policy permits and confidence is sufficient.
2. Profanity-only cannot trigger severe suppression alone.
3. Uncertain/conflicted cases must produce explicit `review_reason_codes`.
4. Judge output is advisory; policy + human review are authoritative.

## Compatibility
1. Stage1Result changes are additive-only.
2. Dashboard/telemetry contracts expand without key removal.
3. Legacy UI cards remain functional during hybrid rollout.

## Canonical References
1. `0.READMEs/research_ground_truth.md`
2. `0.READMEs/pipeline_math_algorithms.md`
3. `docs/research/agent_rubric.md`
