# Municipal Civic Insights Pipeline

## What This Repo Is
Civic Lens is a Streamlit-based architecture mockup for municipal civic feedback analysis.
It simulates how resident comments and reactions move through:
- ingestion and validation
- stage-1 parallel analysis agents
- reviewer correction logic
- stage-2 proposal-level synthesis
- dashboard and architecture telemetry outputs

The current goal is blueprint quality, supervisor feedback, and contract stability before production integrations.

## Quickstart
```powershell
python -m pip install -r requirements.txt
streamlit run app.py
pytest
```

## Docs (Start Here)
- Modular docs index: [0.READMEs/00_index.md](./0.READMEs/00_index.md)
- Research rubric: [docs/research/agent_rubric.md](./docs/research/agent_rubric.md)

## Architecture In 60 Seconds
```text
Resident UI
  -> Ingestion + Validation
     -> Queue + Reaction Counter
        -> Stage-1 Comment Agents (10 parallel mock agents)
           -> Per-comment store + reviewer correction loop
              -> Stage-2 synthesis (topics/trends/summary)
                 -> Dashboard payloads + architecture telemetry
```

## Core Flows
1. Resident submits a comment and reactions in the Streamlit interface.
2. Ingestion validates proposal context and event integrity.
3. Stage-1 runs ten deterministic, research-backed mock agents.
4. Reviewer pass applies correction rules and records auditable changes.
5. Stage-2 synthesizes proposal-level insight and trend summaries.
6. UI renders proposal dashboards and architecture-quality telemetry.

## Project Structure
```text
app.py                          # Streamlit app entrypoint
src/alpha_app/core/             # Pipeline orchestration and analysis logic
src/alpha_app/domain/           # Typed models/contracts
src/alpha_app/ui/               # Charts, theme, and session state
tests/unit/                     # Unit tests
tests/integration/              # Integration tests
docs/                           # Design and research support docs
0.READMEs/                      # Modular operational documentation
conductor/                      # Local-only planning artifacts
```

## Testing
### Unit + Integration
```powershell
pytest
```

### Coverage
```powershell
pytest --cov=src/alpha_app/core --cov=src/alpha_app/domain --cov-report=term-missing
```

## Smoke Test
Use this quick non-UI check to validate pipeline wiring and seeded data:
```python
import bootstrap_path
from alpha_app.core.pipeline import AlphaPipeline
p = AlphaPipeline()
print("cards:", len(p.get_card_summaries()))
print("has_agent_outputs:", "agent_outputs" in p.architecture_metrics())
```
Expected outcome:
- `cards` is greater than `0`
- `has_agent_outputs` is `True`

## Outputs, Artifacts, and Logs
- In-memory pipeline state is owned by `AlphaPipeline` during runtime.
- Artifact outputs are available when pipeline is initialized with `emit_artifacts=True`.
- Coverage output is stored in `.coverage` and displayed in terminal.
- Streamlit runtime logs are shown in the shell running `streamlit run app.py`.

## Configuration Snapshot
- Dependencies: [requirements.txt](./requirements.txt)
- Test defaults and coverage args: [pytest.ini](./pytest.ini)
- Municipality constants: `src/alpha_app/config.py`
- Seeded proposals/comments: `src/alpha_app/core/proposals.py`

## Data Flow Summary
1. UI action creates a `CommentEvent`.
2. Validation enforces non-empty text, known proposal ID, and non-future timestamps.
3. Stage-1 emits `Stage1Result` with `agent_scores` and `agent_labels`.
4. Reviewer logic produces corrected/final rows and correction records.
5. Stage-2 builds `Stage2Insight` and dashboard payloads.
6. Architecture telemetry blocks feed health and quality charts.

## Verification Checklist
- App starts with `streamlit run app.py`.
- Login screen and cards render.
- Proposal detail opens with comments, map, and metrics.
- Dashboard tabs render charts without key/shape errors.
- `pytest` passes.
- Coverage remains above threshold.

## Quick Commands Reference
```powershell
# Unit tests only
pytest tests/unit

# Integration tests only
pytest tests/integration

# Read architecture references
Get-Content docs/architecture/alpha_mapping.md
Get-Content 0.READMEs/architecture.md
```

## Operations
- This is a mockup blueprint phase, not production deployment.
- No production API keys are required for current behavior.
- Conductor artifacts in `conductor/` remain local-only.

## Development Boundaries (Current Phase)
- No live municipal system integrations.
- No production-grade auth/session stack.
- No cloud deployment hardening yet.
- Deterministic scoring is preferred for reproducibility.

## How To Extend Safely
1. Preserve dataclass contracts before changing payload keys.
2. Add failing tests first for any new stage logic.
3. Keep architecture telemetry schema stable for charts.
4. Update relevant docs under `0.READMEs/` when behavior changes.
5. Re-run `pytest` and smoke checks before commit.
