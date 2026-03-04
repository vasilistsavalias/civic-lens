# Research Pipeline Blueprint (Rebuild)

## Purpose
Rebuild the research foundation for a civic text-analysis pipeline that covers sentiment, emotions, irony, argument quality, and safety/civility with concrete math, rules, and guardrails.

## Who Should Read This
Both

## Executive Summary
- Sentiment, stance, emotion, irony, and quality should not be collapsed into one score; they are distinct signals with different failure modes [1][2][3][4].
- A production-ready design should use multi-task outputs, calibrated confidence, and abstention-to-review rules instead of unconditional auto-decisions [5][6].
- Quality assessment should be dimension-based (relevance, evidence, structure, civility) and explicitly separated from toxicity/offense labeling [7][8][9].

## Key Findings (Research-Backed)
- **Sentiment is not stance**: stance needs target conditioning and separate evaluation [4].
- **Emotion should be multi-label or intensity-aware**: shared-task setups include both classification and intensity tasks [2]; fine-grained emotion remains hard (GoEmotions baseline F1 around 0.46) [3].
- **Irony is a separate task**: binary irony detection is easier than fine-grained irony typing (reported top F1 about 0.71 vs 0.51) [10].
- **Tweet-domain pretraining helps**: tweet-specific language models outperform generic baselines on tweet tasks [6][11].
- **Argument quality is multidimensional**: quality contains multiple traits and cannot be represented by length-only heuristics [7][8].
- **Offense is hierarchical**: offensive detection should split presence/type/target, not a single binary label [9][12].
- **Offensive is not always hate**: conflating categories causes precision errors and policy risk [13].
- **Civility/politeness is independently measurable** with lexical/syntactic cues and can be modeled cross-domain [14].

## Detailed Analysis

### 1) Sentiment and Stance
Sentiment answers "positive/neutral/negative tone"; stance answers "for/against/none toward target". Shared-task framing explicitly treats them as complementary, not equivalent [4].

Practical implication for our pipeline:
- Keep separate heads for sentiment and stance.
- Add a consistency feature:
  - `stance_sentiment_conflict = 1` when stance is `against` but sentiment is `positive` (or inverse) with high confidence.
- Review-trigger on high conflict + low confidence.

### 2) Emotions
SemEval Affect in Tweets includes intensity and categorical subtasks in multiple languages [2]. GoEmotions shows fine-grained emotion remains difficult even with BERT [3].

Practical implication:
- Add emotion head as multi-label probabilities over a compact civic taxonomy first:
  - `anger, fear, sadness, joy, trust, disgust, neutral`
- Optional intensity scalar:
  - `emotion_intensity in [0,1]`

### 3) Irony/Sarcasm
Irony has measurable but limited top performance, especially for fine-grained classes [10]. Large sarcasm corpora (SARC) show scale and context matter [15].

Practical implication:
- Keep irony head independent.
- Add rule:
  - if `irony_prob >= 0.65` and `sentiment in {positive, negative}` and stance contradicts tone, down-weight sentiment confidence and route to review.

### 4) Argument Quality
Argument quality literature stresses multiple traits and context effects; intrinsic text-only assessment has moderate, not perfect, success [7]. New datasets provide pointwise and pairwise quality supervision (6.3k arguments + 14k pairs) [8].

Practical implication:
- Use trait vector instead of only one scalar:
  - `relevance, evidence, structure, clarity, civility`
- Keep scalar for dashboards:
  - `quality = w_r*relevance + w_e*evidence + w_s*structure + w_c*clarity + w_v*civility`

### 5) Toxicity, Profanity, Civility
OffensEval/OLID supports a hierarchical annotation design [9][12]. Prior work shows lexical-only hate/offense detection causes category confusion [13]. Politeness modeling adds a separate social-signal channel [14].

Practical implication:
- Split:
  - profanity detection (lexical)
  - offense/toxicity classification
  - target identification (if offensive)
  - civility scoring
- Never use profanity alone as automatic suppression rule.

## Math and Logic for Implementation

### Multi-Task Objective
For shared encoder `h` and task heads:

`L_total = lambda_s * CE(y_sent, p_sent) + lambda_st * CE(y_stance, p_stance) + lambda_e * BCE(y_emotion, p_emotion) + lambda_i * CE(y_irony, p_irony) + lambda_q * MSE(y_quality, q_hat) + lambda_o * CE(y_offense, p_offense)`

Where:
- `CE` = cross-entropy
- `BCE` = binary cross-entropy
- `MSE` = mean squared error

### Calibration
Use temperature scaling for each classification head [5]:

`p_calibrated = softmax(logits / T)`

Track:
- Expected Calibration Error (ECE)
- Brier score

### Abstain / Human-Review Routing
Route to reviewer if any condition holds:
- `max(p_head) < 0.55`
- `entropy(p_head) > 1.0` (for 3-class heads; tune empirically)
- `irony_prob >= 0.65` AND `sentiment_conflict = 1`
- `offense_prob in [0.45, 0.65]` (gray zone)

### Composite Quality Score (Guardrailed)
`quality_score = 0.30*relevance + 0.25*evidence + 0.20*structure + 0.15*clarity + 0.10*civility - 0.15*toxicity`

Clamp to `[0,1]`.

Rationale:
- Relevance/evidence dominate policy usefulness.
- Toxicity penalizes quality but does not auto-zero substantive arguments.

## Rules and Guardrails

### Data and Annotation
- Keep dual annotation for subjective tasks (irony, quality, offense target).
- Track inter-annotator agreement; do not silently merge high-disagreement labels.
- Include adversarial and hard-negative slices (polite disagreement, quoted offense, irony without hashtags).

### Inference Policy
- Do not auto-moderate based on profanity-only signal.
- Separate policy actions from analytic labels.
- Keep per-head outputs and explanations for auditability.

### Evaluation
- Sentiment/stance/offense: Macro-F1 + class-wise recall.
- Emotion: micro-F1 and macro-F1 (multi-label).
- Quality: Spearman/Pearson + pairwise ranking accuracy.
- Calibration: ECE/Brier by head.
- Safety-critical slice: false-positive rate on non-offensive civic criticism.

### Monitoring
- Drift checks on label distributions (weekly).
- Confidence drift and abstain-rate drift alarms.
- Threshold re-tuning only with held-out validation, never on live data.

## Things To Look During Error Analysis
- Sentiment positive but stance against target.
- Irony flip cases where lexical sentiment is misleading.
- Emotional blends (anger + fear) miscast as pure toxicity.
- High-evidence comments penalized excessively for tone.
- Offensive target confusion (group vs individual vs untargeted).

## Suggested Build Order (Pragmatic)
1. Stabilize sentiment + stance + irony + offense with calibration.
2. Add emotion multi-label head.
3. Upgrade argument quality to trait-based outputs.
4. Add abstain/review loop with SLA targets.
5. Introduce multilingual adaptation path (XLM-R baseline + language-specific adapters).

## Confidence
Medium-high for architecture and guardrail recommendations, high for benchmark/task-structure facts reported in cited shared-task papers.

## Sources
[1] SemEval-2017 Task 4: Sentiment Analysis in Twitter. ACL Anthology. https://aclanthology.org/S17-2088/  
[2] SemEval-2018 Task 1: Affect in Tweets. ACL Anthology. https://aclanthology.org/S18-1001/  
[3] GoEmotions: A Dataset of Fine-Grained Emotions. arXiv. https://arxiv.org/abs/2005.00547  
[4] SemEval-2016 Task 6: Detecting Stance in Tweets (task definition/eval). https://alt.qcri.org/semeval2016/task6/  
[5] On Calibration of Modern Neural Networks. PMLR. https://proceedings.mlr.press/v70/guo17a.html  
[6] BERTweet: A pre-trained language model for English Tweets. ACL Anthology. https://aclanthology.org/2020.emnlp-demos.2/  
[7] Intrinsic Quality Assessment of Arguments. ACL Anthology. https://aclanthology.org/2020.coling-main.592/  
[8] Automatic Argument Quality Assessment -- New Datasets and Methods. arXiv. https://arxiv.org/abs/1909.01007  
[9] Predicting the Type and Target of Offensive Posts in Social Media. arXiv. https://arxiv.org/abs/1902.09666  
[10] SemEval-2018 Task 3: Irony Detection in English Tweets. ACL Anthology. https://aclanthology.org/S18-1005/  
[11] TweetEval: Unified Benchmark and Comparative Evaluation for Tweet Classification. ACL Anthology. https://aclanthology.org/2020.findings-emnlp.148/  
[12] SemEval-2019 Task 6 (OffensEval). arXiv. https://arxiv.org/abs/1903.08983  
[13] Automated Hate Speech Detection and the Problem of Offensive Language. arXiv. https://arxiv.org/abs/1703.04009  
[14] A Computational Approach to Politeness with Application to Social Factors. arXiv. https://arxiv.org/abs/1306.6078  
[15] A Large Self-Annotated Corpus for Sarcasm (SARC). arXiv. https://arxiv.org/abs/1704.05579  
[16] HurtLex: A Multilingual Lexicon of Words to Hurt. ACL Anthology. https://aclanthology.org/2018.clicit-1.11/
