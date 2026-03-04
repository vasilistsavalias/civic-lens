# API Contracts

## Purpose
Document callable interfaces that behave like API boundaries, even though this mockup has no external HTTP service yet.

## Who Should Read This
Technical

## Key Concepts
- Pipeline service boundary:
  Practical example: submit_comment(...) acts like POST /comments semantics.
- Card expansion boundary:
  Practical example: open_card(proposal_id) acts like GET /proposals/{id}/detail.
- Dashboard boundary:
  Practical example: uild_dashboard_data(mode, proposal_id, service_filter) acts like dashboard query endpoint.

## Analogy
These functions are internal API endpoints with direct Python calls instead of network transport.

## Key Files and Directories
- src/alpha_app/core/pipeline.py
- src/alpha_app/ui/state.py
- pp.py

## Interfaces and Contracts
- Request-like inputs: IDs, mode flags, filters
- Response-like outputs: dataclass view models and chart-ready rows

## How to Run or Verify
`powershell
pytest tests/integration/test_card_flow_integration.py
`

## Failure Modes and Diagnosis
- Invalid proposal id: validation error in submission or empty expansion.
- Unexpected payload keys: chart functions fail if field names drift.

## Known Tradeoffs and Future Improvements
- Tradeoff: no network/API auth semantics are exercised.
- Future: wrap same contracts behind FastAPI/Flask transport layer.
