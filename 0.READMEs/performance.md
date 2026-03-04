# Performance

## Purpose
Identify key latency/cost drivers in the mock pipeline and define measurable optimization tactics.

## Who Should Read This
Technical

## Key Concepts
- Main latency drivers:
  Practical example: stage-1 scoring and dataframe/chart construction dominate local response time.
- Main cost drivers for future real stack:
  Practical example: LLM inference and storage writes for artifacts will dominate cloud costs.
- Throughput knobs:
  Practical example: batch processing pending events can reduce per-comment overhead.

## Analogy
Performance tuning is traffic engineering: you measure bottlenecks first, then widen the right lanes.

## Key Files and Directories
- src/alpha_app/core/pipeline.py
- src/alpha_app/core/mock_engine.py
- src/alpha_app/ui/charts.py
- 	ests/

## Interfaces and Contracts
- Queue metrics: queue_timeline (depth, 	hroughput).
- Store metrics: store_volume, store_freshness.
- Agent workload proxy: classifier_vs_llm.

## Measurement Plan
- Measure wall-clock latency for:
  - submit_comment(...)
  - _process_pending_for_proposal(...)
  - uild_dashboard_data(...)
- Log per-stage elapsed milliseconds and event counts.
- Track memory usage when rendering advanced dashboard mode.

## Profiling Commands
`powershell
python -m cProfile -o profile.out app.py
pytest --durations=10
`

## Caching Strategy and Invalidation
- Current cache-like behavior: proposal freshness via _dirty_proposals set.
- Invalidation rule: mark proposal dirty on new comment, refresh on access.
- Future: add persisted cache for stage-2 summaries by (proposal_id, time_window).

## Concrete Tuning Knobs
- Queue batch size for pending events per proposal.
- Number of proposal cards auto-refreshed per request.
- Stage-1 lexicon size and regex complexity.
- Plotly trace count in advanced dashboards.

## Failure Modes and Diagnosis
- UI lag after comment bursts: inspect queue depth growth and refresh frequency.
- Slow tests: identify heavy fixtures or repeated pipeline seeding.

## Known Tradeoffs and Future Improvements
- Tradeoff: deterministic Python logic favors explainability over vectorized throughput.
- Future: introduce async processing and optional vectorized text feature extraction.
