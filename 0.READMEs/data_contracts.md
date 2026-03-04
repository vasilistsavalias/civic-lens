# Data Contracts

## Purpose
Define the data shapes, lifecycle, and artifact boundaries for comments, stage-1 results, reviews, and dashboards.

## Who Should Read This
Technical

## Key Concepts
- Event contract:
  Practical example: every comment event requires proposal_id, comment_text, reaction dict, and timestamp.
- Stage-1 enriched output:
  Practical example: each result now includes gent_scores and gent_labels for 10 agents.
- Artifact contract:
  Practical example: initial/final analysis rows and correction logs are serialized into stable paths.

## Analogy
Data contracts are shipping labels; without consistent labels, packages (features) go to the wrong destination.

## Key Files and Directories
- src/alpha_app/domain/models.py
- src/alpha_app/core/artifacts.py
- src/alpha_app/core/pipeline.py
- 	ests/unit/test_artifact_contracts.py

## Interfaces and Contracts
- Input: CommentEvent
- Output stage-1: Stage1Result
- Output stage-2: Stage2Insight
- Dashboard outputs: DashboardOverviewSeries, DashboardProposalSeries

## How to Run or Verify
`powershell
pytest tests/unit/test_artifact_contracts.py
`

## Failure Modes and Diagnosis
- Contract drift: tests fail due key changes between serializer and dataclass schema.
- Missing artifacts: check emit_artifacts=True and writable filesystem.

## Known Tradeoffs and Future Improvements
- Tradeoff: schema versioning is implicit.
- Future: add explicit schema version fields and migration helpers.
