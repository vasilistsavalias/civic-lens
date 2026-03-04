# Glossary

## Purpose
Provide a shared vocabulary for technical and non-technical collaborators.

## Who Should Read This
Both

## Key Concepts
- Stage-1 Agent: component scoring each comment independently.
  Practical example: toxicity agent labels abusive tone probability.
- Stage-2 Synthesis: aggregation of many comment outputs to proposal-level insight.
  Practical example: top topics and trend summaries for one proposal.
- Correction Loop: reviewer logic that adjusts low-trust/contradictory model outputs.

## Analogy
A glossary is the project dictionary so every team member uses the same definitions.

## Terms
- CommentEvent: input record for a resident comment + reactions.
- Stage1Result: per-comment analysis output including labels/scores.
- Stage2Insight: proposal-level synthesized summary.
- CorrectionRecord: auditable change made by reviewer policy.
- Quality Telemetry: rates for corrected/unchanged/unresolved analysis outputs.
- Artifact Contract: predefined filesystem paths and schemas for output files.
- Freshness Lag: time difference between latest comment and generated insight.
- Support Ratio: share of supportive reactions over all reactions.
- Mockup Mode: blueprint phase using synthetic/deterministic behavior.

## Key Files and Directories
- src/alpha_app/domain/models.py
- src/alpha_app/core/review.py

## How to Run or Verify
- Cross-check term usage in architecture/testing docs.

## Failure Modes and Diagnosis
- Vocabulary drift across docs and code comments.
- Ambiguous terms between sentiment/stance/civility in discussions.

## Known Tradeoffs and Future Improvements
- Tradeoff: glossary currently English-first while UI content is Greek-heavy.
- Future: add bilingual glossary entries for supervisor/resident communication.
