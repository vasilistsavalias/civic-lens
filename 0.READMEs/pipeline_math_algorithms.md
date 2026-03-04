# Pipeline Math and Agents (Supervisor Brief)

## One-line Summary
Current system is a deterministic, multi-head Mock++ blueprint; target system is a hybrid cascade (heuristics + model heads + constrained LLM judge + human review) with fairness and evidence-tier governance.

## Agent Count and Roles

### Current implemented Stage-1 agents (11)
1. `sentiment`
2. `stance`
3. `emotion`
4. `irony`
5. `argument_quality`
6. `profanity`
7. `toxicity`
8. `civility`
9. `structure`
10. `evidence`
11. `relevance`

Derived signal: `clarity`.

### Final target runtime topology (14)
1. Heuristic Gate Agent
2. Sentiment Agent
3. Stance Agent
4. Emotion Agent
5. Irony Agent
6. Profanity Agent
7. Toxicity Agent
8. Civility Agent
9. Structure Agent
10. Evidence Agent
11. Relevance Agent
12. Calibration & Uncertainty Agent
13. LLM Adjudication Agent (two-pass)
14. Fairness Auditor Agent

## Are We Using Heuristics in Final Product?
Yes. Heuristics remain first-pass guardrails for:
- normalization,
- lexical priors,
- cheap safety checks,
- fallback behavior.

They are not the sole decision engine in hybrid mode.

## Classifier Strategy
Not a single classifier.
We use a multi-head architecture where each head solves one task and exposes score + label + metadata.

## Core Equations (Current Implementation)
All bounded to `[0,1]`.

- `toxicity = 0.45*profanity + 0.35*insults + 0.10*caps + 0.10*exclamation`
- `civility = 0.60*(1 - toxicity) + 0.40*politeness`
- `evidence = 0.45*reason + 0.35*source + 0.20*numeric`
- `structure = mean(claim, reason, counterargument, length)`
- `quality = 0.30*relevance + 0.25*evidence + 0.20*structure + 0.15*clarity + 0.10*civility - 0.15*toxicity`

Routing thresholds:
- low confidence: `max_prob < 0.55`
- high entropy: `mean_entropy > 0.95`
- offense gray zone: `0.45 <= toxicity <= 0.65`

## What Is Research-Derived vs Heuristic?
- Task decomposition and metric families: mostly Tier A.
- Numeric coefficients and routing thresholds above: currently Tier C defaults.
- Tier metadata is explicit in `src/alpha_app/core/evidence_registry.py`.

## LLM Judge Design (Hybrid)
No single free-form prompt.

Two-pass constrained protocol:
1. Pass A: strict JSON rubric scores + rationale tags.
2. Pass B: consistency + policy checks.

Trigger conditions:
- conflicts,
- uncertainty,
- moderation borderlines.

## Metrics We Report

### Task quality
- Macro-F1 + per-class recall (sentiment/stance/toxicity)
- Emotion multi-label F1
- Quality Pearson/Spearman
- Calibration proxies (ECE/Brier)

### Governance quality
- Abstain rate
- Slice false-positive rate
- Fairness slice metrics (FPR/FNR/TPR/AUC proxy + language gaps)
- Judge reliability proxies
- Evidence coverage by tier

## Versioning / Policy Controls
- `INFERENCE_MODE = mock | hybrid`
- `JUDGE_TRIGGER_POLICY_VERSION`
- `FAIRNESS_POLICY_VERSION`
- `EVIDENCE_REGISTRY_VERSION`

## Canonical Files
- `src/alpha_app/core/evidence_registry.py`
- `src/alpha_app/core/mock_engine.py`
- `src/alpha_app/core/pipeline.py`
- `src/alpha_app/core/judge.py`
- `tools/eval/run_eval.py`
- `0.READMEs/research_ground_truth.md`
