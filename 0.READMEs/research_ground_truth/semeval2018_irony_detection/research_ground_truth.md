# Research Ground Truth

## Source
- **Title:** Van Hee et al. - SemEval-2018 Task 3: Irony Detection in English Tweets
- **Link:** https://aclanthology.org/S18-1005/

## 1) TLDR
Irony is best treated as a dedicated detection task because polarity contrast breaks standard sentiment assumptions.

## 2) Insights Gained
- Lexical sentiment alone misses ironic intent.
- Contrast signals and pragmatic markers are key for irony detection.
- Irony detection should feed downstream corrections in sentiment interpretation.

## 3) Applied To Our Task
- Keep an independent irony flag/score agent rather than embedding irony into sentiment only.
- Preserve irony-aware reviewer override logic for sentiment corrections.
- Add targeted test cases where positive words produce neutral/negative interpretation under irony.
