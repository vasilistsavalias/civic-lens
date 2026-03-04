# Observability

## Purpose
Define how to inspect pipeline health and diagnose behavior across ingestion, analysis, and dashboard generation.

## Who Should Read This
Technical

## Key Concepts
- Built-in telemetry snapshots:
  Practical example: queue depth/throughput snapshots are stored in queue_snapshots.
- Review quality metrics:
  Practical example: correction rate and unresolved rate track reviewer intervention cost.
- Architecture dashboard feed:
  Practical example: rchitecture_metrics() emits chart-ready blocks for reliability views.

## Analogy
Observability is the dashboard of your dashboard pipeline: it tells you if the system itself is healthy.

## Key Files and Directories
- src/alpha_app/core/pipeline.py
- src/alpha_app/core/review.py
- 	ests/unit/test_architecture_metrics.py

## Interfaces and Contracts
- Main telemetry output: AlphaPipeline.architecture_metrics() dict sections:
  - pi_validation, queue_timeline, store_volume, store_freshness, scheduler_triggers, gent_outputs

## How to Run or Verify
`powershell
pytest tests/unit/test_architecture_metrics.py
`

## Failure Modes and Diagnosis
- Empty metrics blocks: ensure seeded data exists and _ensure_fresh() runs before readout.
- Misleading trend lines: check timestamp generation granularity and event ordering.

## Known Tradeoffs and Future Improvements
- Tradeoff: no centralized logging backend yet.
- Future: emit structured logs/metrics to OpenTelemetry-compatible sink.
