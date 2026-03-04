# Research Ground Truth

## Source
- **Title:** Zampieri et al. - Predicting the Type and Target of Offensive Posts in Social Media
- **Link:** https://arxiv.org/abs/1903.08983

## 1) TLDR
Offensive language should be decomposed into offense presence, offense type, and offense target for useful moderation analytics.

## 2) Insights Gained
- Offense detection benefits from layered annotation schemes.
- Targeted abuse differs from untargeted profanity and should not be conflated.
- Fine-grained labeling improves decision utility over single toxic/non-toxic labels.

## 3) Applied To Our Task
- Separate profanity and toxicity agents in our stage-1 design.
- Plan future extension for target-type fields (individual/group/other).
- Use layered outputs in dashboards to avoid overblocking civic disagreement.
