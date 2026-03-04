# Backend

## Purpose
Document core Python pipeline logic that powers ingestion, analysis, and dashboard payload generation.

## Who Should Read This
Technical

## Key Concepts
- Pipeline orchestration:
  Practical example: open_card(proposal_id) ensures stage refresh and returns expanded proposal data.
- Validation gate:
  Practical example: empty text or unknown proposal ID raises a ValueError in alidate_event.
- Telemetry snapshots:
  Practical example: queue depth and throughput snapshots are captured per processing cycle.

## Analogy
The backend is an assembly line where each station adds a label, quality check, or summary before final packaging.

## Key Files and Directories
- src/alpha_app/core/pipeline.py
- src/alpha_app/core/mock_engine.py
- src/alpha_app/core/review.py
- src/alpha_app/core/proposals.py
- src/alpha_app/domain/models.py

## Interfaces and Contracts
- Core class: AlphaPipeline
- Inbound contract: CommentEvent
- Stage-1 contract: Stage1Result
- Stage-2 contract: Stage2Insight

## How to Run or Verify
`powershell
pytest tests/unit/test_pipeline_core.py
pytest tests/unit/test_architecture_metrics.py
`

## Failure Modes and Diagnosis
- Unexpected label outputs: inspect lexicons and thresholds in mock_engine.py.
- Low confidence everywhere: review confidence formula and normalization.
- Review metrics empty: verify _ensure_fresh() and pply_mock_reviewer_pass(...) path.

## Known Tradeoffs and Future Improvements
- Tradeoff: no async queue runtime yet; queue is simulated in-memory.
- Future: introduce true message queue adapter with same event contract.
