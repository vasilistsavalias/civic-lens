# Research Ground Truth

## Source
- **Title:** Rosenthal et al. - SemEval-2017 Task 4: Sentiment Analysis in Twitter
- **Link:** https://aclanthology.org/S17-2088/

## 1) TLDR
Sentiment in social text is noisy, domain-shifted, and often best represented with explicit polarity classes and confidence.

## 2) Insights Gained
- Token-level sentiment cues can be brittle under slang and short-form syntax.
- Shared-task framing shows value of robust baselines plus contextual features.
- Class imbalance and neutral-heavy distributions are common in real deployments.

## 3) Applied To Our Task
- Retain explicit positive/neutral/negative labels and confidence in our payload schema.
- Prepare calibration steps for neutral-heavy civic comments.
- Use this source to justify sentiment-specific tests separate from stance tests.
