# Pipeline Math and Agents (Supervisor Brief)

## Scope (Current Mock++ Phase)
- Mode: deterministic `Mock++` (no production ML model serving yet).
- Languages: Greek + English lexical support.
- Purpose: transparent, testable blueprint before real model swap-in.

## How Many Agents We Use
- Stage-1 agents in code (`AGENT_NAMES`): **11**
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
- Extra derived signal (computed and stored): `clarity` (used in quality formula and telemetry).

## What Our Classifier Is
- Current classifier family: **rule-based multi-head lexical classifier** (`src/alpha_app/core/mock_engine.py`).
- Not a single monolithic classifier. We run one head per task and then combine signals.
- Every head emits:
  - score in `[0,1]` (`agent_scores`)
  - label (`agent_labels`)
  - plus shared confidence/routing metadata.

## Are We Using Heuristics
- **Yes**. Heuristics are the core of Mock++ right now.
- Main heuristic types:
  - accent-normalized token matching (Greek/English lexicons),
  - phrase markers (irony, claims, reasons, politeness),
  - structural features (length, counter-argument markers),
  - style features (caps ratio, exclamation burst),
  - proposal/topic keyword relevance.

## Core Math and Algorithms

### 1) Sentiment / Stance
- Polarity from positive vs negative token counts.
- Stance from pro vs against token counts.
- Labels:
  - sentiment: `positive|neutral|negative`
  - stance: `for|neutral|against`

### 2) Emotion (Multi-label)
- Emotions: `anger,fear,sadness,joy,trust,disgust,neutral`.
- Per-label score from keyword hit share.
- Intensity:
  - `emotion_intensity = clamp(total_emotion_hits / 4, 0, 1)`

### 3) Safety Split
- `profanity_score = clamp(profanity_hits / 2, 0, 1)`
- `toxicity_score = clamp(0.45*profanity + 0.35*insults + 0.10*caps_ratio + 0.10*exclamation_burst, 0, 1)`
- `civility_score = clamp(0.60*(1 - toxicity_score) + 0.40*politeness_signal, 0, 1)`
- `offense_target`: `individual|group|untargeted|unknown` (placeholder logic active).

### 4) Argument Traits
- `evidence_score = 0.45*reason_markers + 0.35*source_markers + 0.20*numeric_signal`
- `structure_score = mean(claim_signal, reason_signal, counter_signal, length_signal)`
- `relevance_score` from proposal/topic keyword hits
- `clarity_score = 0.5*clarity_markers + 0.5*length_signal`

### 5) Composite Quality Score
- Implemented formula:
- `quality_score = clamp(0.30*relevance + 0.25*evidence + 0.20*structure + 0.15*clarity + 0.10*civility - 0.15*toxicity, 0, 1)`
- Stored as `argument_quality_score` for backward compatibility.

### 6) Calibration
- Temperature scaling interface per head (`src/alpha_app/core/calibration.py`):
- `p_cal = sigmoid(logit(p_raw) / T)`
- Outputs saved in `calibrated_scores`.

### 7) Abstain / Review Routing (Balanced Policy)
- Triggers:
  - low confidence: `max_prob < 0.55`
  - high entropy: `mean_entropy > 0.95`
  - irony/sentiment/stance conflicts
  - offense gray zone: `0.45 <= toxicity <= 0.65`
- Emits:
  - `abstain_flags`
  - `conflict_flags`
  - `review_reason_codes`
- Guardrail: profanity-only signal does not auto-suppress by itself.

### 8) Reaction Scoring (Discussion Feed Logic)
- `total_reacts = sum(reactions)`
- `signed_score_raw = Σ(weight[r] * count[r])`
- `signed_score_norm = tanh(signed_score_raw / max(1,total_reacts))`
- Dual use:
  - raw magnitude for queue/action context,
  - normalized score for ranking/display.

## Metrics We Track

### Evaluation Harness (`tools/eval/run_eval.py`)
- Macro-F1: sentiment, stance, toxicity.
- Per-class recall: sentiment, stance, toxicity.
- Multi-label emotion F1 (micro).
- Quality correlation: Pearson, Spearman.
- Calibration proxies: ECE proxy, Brier proxy.
- Operational: abstain rate, slice false-positive rate (`non_offensive_criticism`).

### Runtime / Architecture Telemetry (`pipeline.architecture_metrics`)
- `calibration_metrics`
- `abstain_summary`
- `conflict_summary`
- `emotion_distribution`
- plus queue/store/scheduler/validation blocks.

## What Changes Later (Real Model Phase)
- Keep same contract (`Stage1Result` keys stay stable).
- Swap rule-based heads with trained models per head.
- Refit thresholds/calibration using labeled data.
- Keep guardrails and evaluation suite unchanged as governance backbone.

## Source Pointers
- Research citations and source-by-source mapping:
  - `0.READMEs/research_ground_truth.md`
- Rubric for stage-1 agents:
  - `docs/research/agent_rubric.md`
- Implementation:
  - `src/alpha_app/core/mock_engine.py`
  - `src/alpha_app/core/calibration.py`
  - `src/alpha_app/core/pipeline.py`
