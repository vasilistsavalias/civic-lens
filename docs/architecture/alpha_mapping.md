# Alpha Architecture Mapping (Card-First Revision)

## Core Interaction
- Landing page shows exactly 3 proposal cards.
- Clicking one card opens an inline social-style expanded post.
- Opening a card automatically runs pending pipeline stages for that proposal.

## System Mapping
- Card click orchestration -> `AlphaPipeline.open_card(proposal_id)`
- Ingestion/validation -> `submit_comment(...)` + `validate_event(...)`
- Stage 1 agent simulation -> `classify_stage1(...)`
- Reviewer correction pass -> `apply_mock_reviewer_pass(...)`
- Stage 2 aggregation -> `_build_insight(...)` from reviewed rows
- Artifact contract emission -> `PipelineArtifacts` via pipeline stage hooks
- Freshness policy -> `_dirty_proposals` + `_ensure_fresh(...)`
- Dashboard chart contract -> `build_dashboard_data(mode, proposal_id, service_filter)`

## Artifact Contract Mapping (Mock Blueprint)
- Run root: `artifacts/pipeline_runs/<run_id>/`
- Proposal stage folders:
  - `raw/comments.json`
  - `segments/comment_segments.json`
  - `analysis/initial/stage1_results.json` + `.csv`
  - `analysis/final/stage1_results.json` + `.csv`
  - `analysis/final/corrections.json`
  - `analysis/final/review_metrics.json`
  - `analysis/final/stage2_insight.json`
  - `analysis/visuals/dashboard_<mode>.json`

## UI Mapping
- Card-first interface + dashboards: `app.py`
- Chart factory functions: `src/alpha_app/ui/charts.py`
- Theme/style layer: `src/alpha_app/ui/theme.py`
- Polygon map filtering: `app.py` with `pydeck.PolygonLayer`

## Constraints
- Streamlit-only application stack.
- No real queue/database/model serving in this alpha.
- Dashboard surfaces charts only (+ one-line insights).

