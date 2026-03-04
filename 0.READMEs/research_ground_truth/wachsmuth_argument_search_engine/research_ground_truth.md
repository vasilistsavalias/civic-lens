# Research Ground Truth

## Source
- **Title:** Wachsmuth et al. - Building an Argument Search Engine for the Web
- **Link:** https://aclanthology.org/E17-1017/

## 1) TLDR
Large-scale argument mining needs modular quality dimensions and retrieval-oriented ranking, not single-score heuristics.

## 2) Insights Gained
- Argument quality is multi-dimensional and task-dependent (persuasiveness, clarity, relevance, support).
- Operational systems should separate retrieval from argument assessment features.
- Ranking pipelines benefit from explicit quality features that can be inspected and tuned.

## 3) Applied To Our Task
- Keep our argument-quality agent decomposed into relevance/evidence/structure/civility rather than one opaque score.
- Preserve interpretable per-dimension outputs in stage artifacts for supervisor validation.
- Use this source to justify weighted quality formulas in mockup stage and future learned rankers.
