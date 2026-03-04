# Testing

## Purpose
Document test strategy, commands, and how to validate architecture behavior safely.

## Who Should Read This
Technical

## Key Concepts
- Unit coverage for core contracts:
  Practical example: artifact and review policy tests enforce payload shape.
- Integration flow checks:
  Practical example: card-open flow verifies end-to-end recomputation path.
- Coverage threshold intent:
  Practical example: workflow target is >80%, current reports exceed this.

## Analogy
Tests are guardrails on a mountain road: they do not drive the car, but they keep refactors from falling off the edge.

## Key Files and Directories
- pytest.ini
- 	ests/unit/
- 	ests/integration/

## Interfaces and Contracts
- Unit tests validate dataclasses, stage outputs, and policy rules.
- Integration tests validate cross-module behavior through pipeline entrypoints.

## How to Run or Verify
`powershell
pytest
pytest tests/unit/test_stage1_research_agents.py
pytest tests/integration/test_card_flow_integration.py
`

## Failure Modes and Diagnosis
- Failing coverage gate: review newly added modules without test mirrors.
- Encoding-related assertion errors: verify UTF-8 normalization in edited files.

## Known Tradeoffs and Future Improvements
- Tradeoff: no performance/regression benchmark suite yet.
- Future: add deterministic benchmark fixtures and threshold-based CI checks.
