# Research Ground Truth

## Purpose
Single canonical source for research backing, equations, and policy claims in Civic Lens.
This file explicitly separates:
- what is **directly research-backed**,
- what is **locally derived**, and
- what is currently **heuristic**.

## Evidence Tier Policy (Canonical)
- `Tier A (Direct Research)`: definitions/algorithms directly supported by peer-reviewed literature.
- `Tier B (Derived Local Fit)`: calibrated on local labeled civic data.
- `Tier C (Heuristic Default)`: engineering default pending local fit.

Rules:
1. Every decision-critical numeric constant must have `tier + rationale + owner + updated_on + citations + migration_path`.
2. Tier C constants must have explicit migration path to Tier B.
3. Peer-reviewed-first citation policy is canonical; preprints are supplementary only.

## Current Pipeline State (Mock++)
Research-backed now:
- Multi-head task decomposition (sentiment, stance, emotion, irony, safety split, argument traits).
- Calibration family (temperature scaling interface).
- Evaluation families (Macro-F1, per-class recall, emotion F1, Pearson/Spearman, calibration proxies).
- Uncertainty routing and human review design.

Not fully research-parameterized yet:
- Formula coefficients and threshold cutoffs are mostly Tier C defaults.
- They are documented and tracked in `src/alpha_app/core/evidence_registry.py`.

## Core Algorithms and Mapping

### 1) Sentiment (Tier A task framing)
- Labels: `positive|neutral|negative`.
- Research anchors: SemEval-2017 Task 4.

### 2) Stance (Tier A task framing)
- Labels: `for|against|neutral`.
- Independent from sentiment.
- Research anchors: SemEval-2016 Task 6.

### 3) Emotion (Tier A task framing)
- Multi-label emotion scores + intensity.
- Labels: `anger,fear,sadness,joy,trust,disgust,neutral`.
- Research anchors: SemEval-2018 Affect, GoEmotions.

### 4) Irony (Tier A task framing)
- Dedicated irony head; not inferred from sentiment alone.
- Research anchors: SemEval-2018 Task 3, SARC.

### 5) Safety split (Tier A taxonomy + Tier C parameters)
- Distinct outputs: profanity, toxicity, civility, offense target.
- Research anchors: OffensEval, Davidson et al., HurtLex, computational politeness.

### 6) Argument quality (Tier A concept + Tier C weights)
- Trait-vector composition: relevance/evidence/structure/clarity/civility with toxicity penalty.
- Research anchors: intrinsic argument quality literature + argument mining.

### 7) Calibration and uncertainty (Tier A method + Tier C thresholds)
- Temperature scaling API and entropy/confidence routing.
- Research anchor: Guo et al. calibration.

### 8) Fairness auditing (Tier A governance direction + Tier C operational defaults)
- Slice-based toxicity error reporting and language gap summaries.
- Counterfactual fairness template suite in roadmap.

### 9) LLM adjudication (Hybrid mode scaffolding)
- Two-pass constrained judge flow:
  - Pass A rubric JSON + rationale tags.
  - Pass B consistency/policy checks.
- Triggered only on uncertainty/conflict/borderline cases.

## New Peer-Reviewed Expansion (Supervisor Scope)
1. G-Eval (EMNLP 2023): https://aclanthology.org/2023.emnlp-main.153/
2. Humans or LLMs as the Judge? (EMNLP 2024): https://aclanthology.org/2024.emnlp-main.474/
3. Dialectal Toxicity Detection (Findings EMNLP 2025): https://aclanthology.org/2025.findings-emnlp.664/
4. Whose Emotions and Moral Sentiments do LMs Reflect? (Findings ACL 2024): https://aclanthology.org/2024.findings-acl.395/
5. Annotators with Attitudes (NAACL 2022): https://aclanthology.org/2022.naacl-main.431/
6. Simple LLM Prompting for Robust/Multilingual Evaluation (DSTC 2023): https://aclanthology.org/2023.dstc-1.16/

Supplementary preprint:
- MT-Bench / LLM-as-a-Judge: https://arxiv.org/abs/2306.05685

## Baseline Citation Set (Task Foundations)
- SemEval-2017 Task 4 (sentiment): https://aclanthology.org/S17-2088/
- SemEval-2016 Task 6 (stance): https://aclanthology.org/S16-1003/
- SemEval-2018 Task 1 (affect): https://aclanthology.org/S18-1001/
- SemEval-2018 Task 3 (irony): https://aclanthology.org/S18-1005/
- GoEmotions: https://arxiv.org/abs/2005.00547
- OffensEval-2019: https://arxiv.org/abs/1903.08983
- Davidson et al.: https://arxiv.org/abs/1703.04009
- HurtLex: https://aclanthology.org/2018.clicit-1.11/
- Computational Politeness: https://aclanthology.org/W13-3905/
- Argument structure (Stab & Gurevych): https://aclanthology.org/J17-3005/
- Argument quality (COLING 2020): https://aclanthology.org/2020.coling-main.592/
- Argument quality methods/datasets: https://arxiv.org/abs/1909.01007
- Calibration (Guo et al.): https://proceedings.mlr.press/v70/guo17a.html
- TweetEval benchmark framing: https://aclanthology.org/2020.findings-emnlp.148/

## Research-to-Code Anchors
- Evidence registry and tiered constants:
  - `src/alpha_app/core/evidence_registry.py`
- Stage-1 scoring and metadata:
  - `src/alpha_app/core/mock_engine.py`
- Routing, hybrid judge trigger, telemetry:
  - `src/alpha_app/core/pipeline.py`
- Judge scaffolding:
  - `src/alpha_app/core/judge.py`
- Eval harness with fairness/judge/evidence sections:
  - `tools/eval/run_eval.py`

## Defensibility Statement
Civic Lens now has a traceable path from research claims to implementation artifacts.
Where coefficients are still heuristic (Tier C), they are explicitly labeled and versioned, with migration path to local fitted values (Tier B).
