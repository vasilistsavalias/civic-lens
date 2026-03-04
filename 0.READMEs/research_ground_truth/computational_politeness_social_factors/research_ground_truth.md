# Research Ground Truth

## Source
- **Title:** Danescu-Niculescu-Mizil et al. - A Computational Approach to Politeness with Application to Social Factors
- **Link:** https://aclanthology.org/W13-3905/

## 1) TLDR
Politeness can be measured using pragmatic cues and supports a separate civility signal beyond sentiment polarity.

## 2) Insights Gained
- Politeness markers are detectable and correlate with interaction outcomes.
- Civility should be modeled independently from positivity/negativity.
- Pragmatic cues can support interpretable moderation and quality scoring.

## 3) Applied To Our Task
- Maintain a dedicated civility agent using politeness and anti-toxicity signals.
- Include civility contribution inside argument-quality scoring.
- Use civility thresholds to reduce offputting resident experience while allowing disagreement.
