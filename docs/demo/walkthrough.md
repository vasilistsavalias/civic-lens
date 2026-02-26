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
6. Scroll to **Architecture Coverage Graph Mockups** and verify:
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

## Publish (When Approved)
Deploy to Streamlit Community Cloud with `app.py` as entrypoint.
