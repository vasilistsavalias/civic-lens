# Architecture

## Purpose
Explain the end-to-end system shape and how components exchange data.

## Who Should Read This
Both

## Key Concepts
- Two-stage analysis pipeline:
  Practical example: a single comment first gets 10 stage-1 agent scores, then contributes to stage-2 proposal summaries.
- Reviewer correction loop:
  Practical example: irony can trigger a sentiment correction before dashboard aggregation.
- Artifact contracts:
  Practical example: analysis outputs are emitted in stable JSON/CSV paths for reproducibility.

## Analogy
Think of the system as a city planning control room: raw resident messages arrive like phone calls, are categorized by specialized operators, then summarized into decision dashboards.

## Key Files and Directories
- pp.py
- src/alpha_app/core/pipeline.py
- src/alpha_app/core/mock_engine.py
- src/alpha_app/core/review.py
- src/alpha_app/core/artifacts.py
- src/alpha_app/domain/models.py
- docs/architecture/alpha_mapping.md

## Interfaces and Contracts
- Input: CommentEvent submitted via AlphaPipeline.submit_comment(...).
- Intermediate: Stage1Result with agent labels/scores, confidence, tags.
- Output: DashboardOverviewSeries and DashboardProposalSeries for UI charts.

## How to Run or Verify
`powershell
pytest
streamlit run app.py
`
Verify in UI:
- cards render
- proposal detail opens
- architecture charts populate

## Failure Modes and Diagnosis
- Empty dashboards: inspect AlphaPipeline.seed_demo_data() and pipeline refresh path.
- Missing chart data: check uild_dashboard_data(...) outputs and chart field names.
- Broken artifacts: run artifact contract tests in 	ests/unit/test_artifact_contracts.py.

## Known Tradeoffs and Future Improvements
- Tradeoff: deterministic heuristics are transparent but not robust to open-domain language variety.
- Future: replace heuristic agents with model-backed components while retaining current schema.
