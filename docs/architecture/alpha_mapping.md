# Alpha Architecture Mapping (Card-First Revision)

## Core Interaction
- Landing page shows exactly 3 proposal cards.
- Clicking one card opens an inline social-style expanded post.
- Opening a card automatically runs pending pipeline stages for that proposal.

## System Mapping
- Card click orchestration -> `AlphaPipeline.open_card(proposal_id)`
- Ingestion/validation -> `submit_comment(...)` + `validate_event(...)`
- Stage 1 agent simulation -> `classify_stage1(...)`
- Stage 2 aggregation -> `_build_insight(...)`
- Freshness policy -> `_dirty_proposals` + `_ensure_fresh(...)`
- Dashboard chart contract -> `build_dashboard_data(mode, proposal_id, service_filter)`

## UI Mapping
- Card-first interface + dashboards: `app.py`
- Chart factory functions: `src/alpha_app/ui/charts.py`
- Theme/style layer: `src/alpha_app/ui/theme.py`
- Polygon map filtering: `app.py` with `pydeck.PolygonLayer`

## Constraints
- Streamlit-only application stack.
- No real queue/database/model serving in this alpha.
- Dashboard surfaces charts only (+ one-line insights).

