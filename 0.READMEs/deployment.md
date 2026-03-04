# Deployment

## Purpose
Describe current runtime/deployment posture for mockup usage and likely production migration path.

## Who Should Read This
Both

## Key Concepts
- Local-first execution:
  Practical example: Streamlit app and tests run directly from developer machine.
- Mockup lifecycle:
  Practical example: architecture and scoring behavior are validated before external integrations.
- Future portability:
  Practical example: contracts are framework-agnostic so transport/runtime can change later.

## Analogy
Current deployment is a rehearsal stage: same script as production intent, simpler lighting and audience size.

## Key Files and Directories
- README.md
- equirements.txt
- .github/ (if workflows are enabled in this clone)

## Interfaces and Contracts
- Runtime command contract:
  - app: streamlit run app.py
  - tests: pytest

## How to Run or Verify
`powershell
python -m pip install -r requirements.txt
streamlit run app.py
pytest
`

## Failure Modes and Diagnosis
- Dependency install failure: verify Python version and pip environment.
- Port conflicts: run Streamlit on another port (--server.port 8502).

## Known Tradeoffs and Future Improvements
- Tradeoff: no containerized runtime baseline yet.
- Future: add Dockerfile + CI smoke pipeline for reproducible environments.
