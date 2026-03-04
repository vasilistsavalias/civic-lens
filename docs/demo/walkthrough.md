# Supervisor Walkthrough (Card-First Thessaloniki Alpha)

## Run
1. Install dependencies:
   - `python -m pip install -r requirements.txt`
2. Start app:
   - `streamlit run app.py`

## Demo Path
1. Confirm landing shows exactly 3 proposal cards.
2. Click each card:
   - Verify inline expansion (social post style)
   - Verify proposal info, timeline, budget, links, and comments/reactions
3. In expanded section, change service filters and validate polygon map updates.
4. Open dashboards section:
   - Overview Dashboard tab: all cross-proposal graphs
   - Proposal Dashboard tab: selected proposal graphs
5. Toggle Basic/Advanced:
   - Basic: cleaner chart set
   - Advanced: deeper chart detail (e.g., violin quality chart)
6. Verify artifact blueprint output under `artifacts/pipeline_runs/<run_id>/`:
   - Confirm `raw`, `segments`, `analysis/initial`, `analysis/final`, and `analysis/visuals` files exist for each proposal
   - Confirm initial/final stage files are present (`stage1_results.*`, `corrections.json`, `review_metrics.json`, `stage2_insight.json`)
7. In dashboards, verify quality telemetry charts:
   - Overview: review quality overview
   - Proposal: correction rates, review state mix, review lag
8. Scroll to **Architecture Coverage Graph Mockups** and verify:
   - Agent outputs + confidence
   - Classifier vs LLM split
   - API validation outcomes
   - Queue depth/throughput
   - Bypass vs NLP path
   - Store volume + freshness/lag
   - Scheduler trigger charts

## Acceptance Snapshot
- No manual processing buttons.
- Card open auto-triggers pipeline freshness.
- No JSON dumps in UI.
- Graphs-first dashboards with one-line insights.
- Artifact contract files are generated as mock blueprint outputs.
- Reviewer correction and quality telemetry are visible as mock governance signals.

## Publish (When Approved)
Deploy to Streamlit Community Cloud with `app.py` as entrypoint.
