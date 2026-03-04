# Comment Journey Through the Civic Lens Pipeline

## Purpose

This document is the exact story you can present to your supervisor: what happens when **one comment** enters the system, pass by pass, including algorithms, thresholds, and outputs.

## TL;DR Flow

1. Ingestion + validation
2. Stage-1 multi-head analysis (11 agents + clarity)
3. Calibration pass
4. Abstain/conflict/review routing
5. Hybrid judge pass (only in hybrid mode)
6. Review pass + correction metrics
7. Feed/dashboard materialization
8. Artifact + telemetry + evaluation reporting

---

## Super Simple Trace (Like You Asked)

Think of this like a packet moving through a network.

Input comment:

```text
"Great plan, yeah right /s. I oppose this strongly because traffic data from 2025 report shows risks."
```

### Pass 0: Ingestion

- System receives comment and proposal id.
- Checks: text not empty, proposal exists, timestamp valid.
- Result: `CommentEvent` accepted and queued.

Mini output:

```json
{
  "accepted": true,
  "queued": true,
  "comment_id": "c_12345"
}
```

### Pass 1: Heuristic Heads (Rule Engine)

- Tokenizer sees words like:
  - `great` -> positive signal
  - `oppose` -> against stance signal
  - `yeah right`, `/s` -> irony signal
  - `because`, `data`, `2025`, `report` -> evidence signal
- Heads produce labels + scores.

Mini output:

```json
{
  "sentiment": "neutral",
  "stance": "against",
  "irony_flag": true,
  "agent_scores": {
    "evidence": 0.8,
    "toxicity": 0.1,
    "argument_quality": 0.62
  }
}
```

### Pass 2: Calibration

- Raw scores are adjusted to safer confidence values.
- Example: confidence is normalized via temperature scaling.

Mini output:

```json
{
  "calibrated_scores": {
    "sentiment": 0.54,
    "stance": 0.71,
    "irony": 0.83
  }
}
```

### Pass 3: Routing (Should we escalate?)

- Rules check:
  - low confidence?
  - high entropy?
  - conflict (irony + stance/sentiment mismatch)?
  - gray zone toxicity?
- If any true -> add review reason code.

Mini output:

```json
{
  "abstain_flags": {
    "irony_conflict": true,
    "low_confidence": false
  },
  "review_reason_codes": [
    "REVIEW_IRONY_CONFLICT"
  ]
}
```

### Pass 4: Hybrid Judge (Only if Hybrid Mode ON)

- If `INFERENCE_MODE=hybrid` and case is uncertain/conflicted:
  - Pass A: rubric JSON
  - Pass B: consistency check
- Adds judge metadata only.

Mini output:

```json
{
  "judge_invoked": true,
  "judge_decision_id": "judge_ab12cd34ef56",
  "review_reason_codes": [
    "REVIEW_IRONY_CONFLICT",
    "REVIEW_JUDGE_ESCALATION"
  ]
}
```

### Pass 5: Review Pass

- Reviewer layer may correct final interpretation.
- Example: irony can downgrade overly positive sentiment.

Mini output:

```json
{
  "review_status": "corrected",
  "final_sentiment": "neutral"
}
```

### Pass 6: UI + Dashboard

- Final row appears in thread.
- Right panel metrics update (risk, queue pressure, concerns).

### Pass 7: Reports

- Evaluation files update with:
  - F1 metrics
  - fairness gaps
  - judge reliability
  - evidence coverage

If you want one sentence for your supervisor:
> “Comment comes in, heuristics extract structured signals, calibration normalizes confidence, conflict logic decides escalation, optional hybrid judge handles hard cases, reviewer finalizes, then governance metrics are reported.”

---

## Example Input Comment

```text
"Great plan, yeah right /s. I oppose this strongly because traffic data from 2025 report shows risks."
```

Context:

- `proposal_id = metro_west`
- `submitted_at = 2026-03-01 12:00:00`
- reactions initially empty or low

This is intentionally mixed: positive token + irony + against stance + evidence language.

---

## Pass 0: Ingestion + Validation

Where:

- `AlphaPipeline.submit_comment(...)` in `src/alpha_app/core/pipeline.py`
- `validate_event(...)` in `src/alpha_app/core/mock_engine.py`

What happens:

1. Reaction keys are normalized (`likes/support/laugh` -> canonical keys).
2. Thread depth and parent consistency are checked.
3. Proposal id must exist.
4. Comment cannot be empty and cannot be future-dated.
5. Event is queued (`pending_events`) and indexed (`comment_index`).

Output after this pass:

- A valid `CommentEvent` exists in queue/storage, but no NLP decision yet.

---

## Pass 1: Stage-1 Multi-Head Analysis (Deterministic Mock++)

Where:

- `classify_stage1(...)` in `src/alpha_app/core/mock_engine.py`

Heads run in parallel-style logic on normalized tokens:

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

+ derived `clarity`

### Key internals

Normalization:

- lowercase + accent strip + token split.

Core formulas:

- `toxicity = 0.45*profanity + 0.35*insults + 0.10*caps + 0.10*exclamation`
- `civility = 0.60*(1-toxicity) + 0.40*politeness`
- `evidence = 0.45*reason + 0.35*source + 0.20*numeric`
- `structure = mean(claim, reason, counter, length)`
- `quality = 0.30*relevance + 0.25*evidence + 0.20*structure + 0.15*clarity + 0.10*civility - 0.15*toxicity`

Output object:

- `Stage1Result` with:
  - labels (`agent_labels`)
  - scores (`agent_scores`)
  - emotion distribution/intensity
  - offense target placeholder
  - evidence tier metadata (`evidence_tier_by_signal`, `signal_rationale_refs`)
  - fairness slice keys (`lang:*`, `offense_target:*`)

---

## Pass 2: Calibration

Where:

- `calibrate_scores(...)` in `src/alpha_app/core/calibration.py`
- `_enrich_stage1_result(...)` in `src/alpha_app/core/pipeline.py`

What happens:

1. Raw head probabilities are temperature-scaled:
   - `p_cal = sigmoid(logit(p_raw)/T)`
2. `calibrated_scores` are attached to `Stage1Result`.
3. Entropy is computed on selected heads (`sentiment, stance, irony, toxicity, emotion`).

Why:

- Confidence numbers become more policy-usable than raw head outputs.

### How this connects to one comment decision

Assume one comment gets these raw head confidences:

- `sentiment_raw = 0.62`
- `stance_raw = 0.58`
- `irony_raw = 0.51`

After temperature scaling with `T=1.5`, they become less sharp:

- `sentiment_cal ~= 0.59`
- `stance_cal ~= 0.56`
- `irony_cal ~= 0.50`

Routing then reads the calibrated values:

- if `max_prob < 0.55` -> add `REVIEW_LOW_CONFIDENCE`
- if entropy is high (`> 0.95`) -> add `REVIEW_HIGH_ENTROPY`

Example:

- `max_prob = 0.56` -> no low-confidence flag by this rule.
- `max_prob = 0.53` -> low-confidence flag is raised.

Important distinction:

- **Temperature is used during per-comment inference** (real-time routing input).
- **Bins are used during evaluation only** to compute ECE over many comments:
  - split predictions into confidence ranges (for example 15 bins),
  - compare average confidence vs observed accuracy per bin,
  - use the gap to decide whether calibration/thresholds need retuning.

---

## Pass 3: Abstain / Conflict / Review Routing

Where:

- `_enrich_stage1_result(...)` in `src/alpha_app/core/pipeline.py`

Triggers:

- low confidence: `max_prob < 0.55`
- high entropy: `mean_entropy > 0.95`
- irony conflict
- offense gray zone: `0.45 <= toxicity <= 0.65`
- policy block (guardrail logic)

Guardrail:

- Profanity-only signal does not auto-block by itself.

Outputs added:

- `abstain_flags`
- `conflict_flags`
- `review_reason_codes` (e.g., `REVIEW_LOW_CONFIDENCE`, etc.)

---

## Pass 4: Hybrid Judge (Only if `INFERENCE_MODE=hybrid`)

Where:

- `run_two_pass_judge(...)` in `src/alpha_app/core/judge.py`

When invoked:

- conflict / uncertainty / borderline moderation conditions.

Two-pass scaffold:

1. Pass A: rubric-like JSON scores + rationale tags.
2. Pass B: consistency/policy checks.

Outputs added:

- `judge_invoked`
- `judge_decision_id`
- extra review reason: `REVIEW_JUDGE_ESCALATION` when applicable.

Important:

- Judge is advisory escalation logic, not sole final policy authority.

---

## Pass 5: Review Pass

Where:

- `apply_mock_reviewer_pass(...)` in `src/alpha_app/core/review.py`

What happens:

1. Builds initial review row (sentiment, stance, quality, topics, safety, etc.).
2. Applies deterministic reviewer corrections (e.g., irony-aware adjustments).
3. Sets review status:
   - `corrected`
   - `unchanged`
   - `unresolved`
4. Computes review metrics:
   - correction rate
   - unresolved rate
   - lag
   - per-indicator correction rates

Outputs:

- `analysis/initial/stage1_results.*`
- `analysis/final/stage1_results.*`
- `analysis/final/corrections.json`
- `analysis/final/review_metrics.json`

---

## Pass 6: Feed Materialization (UI-ready Row)

Where:

- `discussion_feed(...)` in `src/alpha_app/core/pipeline.py`

What happens:

1. Sort + filter + pagination on thread graph.
2. Injects analysis fields into each visible row:
   - sentiment/stance/quality
   - emotion/irony/safety
   - abstain/conflict/review reasons
   - judge fields
3. Row is rendered in nested expandable UI.

---

## Pass 7: Dashboard + Architecture Telemetry

Where:

- `architecture_metrics()` in `src/alpha_app/core/pipeline.py`

Generated blocks include:

- `calibration_metrics`
- `abstain_summary`
- `conflict_summary`
- `emotion_distribution`
- `judge_reliability`
- `fairness_summary`
- `evidence_coverage`

These are the supervisor-visible technical governance signals.

---

## Pass 8: Evaluation Harness (Public+Mock)

Where:

- `tools/eval/run_eval.py`

Metrics produced:

- Macro-F1 + per-class recall (sentiment/stance/toxicity)
- Emotion micro-F1
- Quality Pearson/Spearman
- ECE/Brier proxies
- Abstain rate
- Slice FPR
- Fairness gaps (FPR/FNR/TPR/AUC proxy)
- Judge reliability proxies
- Evidence coverage ratios

Outputs:

- `docs/research/eval_reports/latest_report.json`
- `docs/research/eval_reports/latest_report.md`

---

## One-line Explanation You Can Say in the Meeting

"Each comment goes through deterministic multi-head analysis, calibration, uncertainty/conflict routing, optional two-pass judge escalation in hybrid mode, reviewer correction, and finally governance reporting with fairness and evidence-tier traceability."

## Related Docs

- `0.READMEs/final_system_spec.md`
- `0.READMEs/pipeline_math_algorithms.md`
- `0.READMEs/research_ground_truth.md`
