# Research Ground Truth

## Source
- **Title:** Davidson et al. - Automated Hate Speech Detection and the Problem of Offensive Language
- **Link:** https://arxiv.org/abs/1703.04009

## 1) TLDR
Offensive language and hate speech are not equivalent; conflation produces systematic labeling errors.

## 2) Insights Gained
- Annotation quality and category boundaries strongly affect model behavior.
- Profanity presence alone is insufficient evidence of hate content.
- Context and target are needed for defensible harm classification.

## 3) Applied To Our Task
- Avoid treating all profanity as high-toxicity by default in our formulas.
- Keep toxic score as multi-signal (insult/profanity/style) rather than lexicon-only.
- Document this distinction to supervisor as core policy choice for civic participation UX.
