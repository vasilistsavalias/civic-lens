# Research Ground Truth

## Source
- **Title:** Mohammad et al. - SemEval-2016 Task 6: Detecting Stance in Tweets
- **Link:** https://aclanthology.org/S16-1003/

## 1) TLDR
Stance is distinct from sentiment; target-aware polarity toward a proposition should be modeled independently.

## 2) Insights Gained
- A text can be positive in tone but against a specific target.
- Target conditioning is mandatory for robust stance assignment.
- Lexical and contextual cues both matter in short social texts.

## 3) Applied To Our Task
- Keep stance and sentiment as separate agents in stage-1 outputs.
- Evaluate stance against proposal context, not only generic tone words.
- Use separate confidence scores for stance and sentiment in telemetry.
