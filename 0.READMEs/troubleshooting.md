# Troubleshooting

## Purpose
Provide fast diagnosis paths for common runtime, test, and data-shape issues.

## Who Should Read This
Both

## Key Concepts
- Reproducible failures:
  Practical example: always rerun failing test directly before changing code.
- Contract-first debugging:
  Practical example: inspect dataclass fields when chart rendering fails.
- Encoding hygiene:
  Practical example: mojibake indicates file encoding drift rather than logic failure.

## Analogy
Troubleshooting is detective work: secure evidence first (logs/tests), then change one variable at a time.

## Key Files and Directories
- src/alpha_app/core/
- src/alpha_app/ui/
- 	ests/
- docs/research/

## Interfaces and Contracts
- If UI fails, verify uild_dashboard_data(...) output keys match chart expectations.
- If submission fails, verify alidate_event(...) constraints.

## How to Run or Verify
`powershell
pytest -q
streamlit run app.py
`

## Failure Modes and Diagnosis
- ValueError: Unknown proposal_id: input proposal ID not in seeded catalog.
- Empty architecture charts: no stage refresh or telemetry snapshots not populated yet.
- Garbled Greek text: re-save edited files as UTF-8.

## Known Tradeoffs and Future Improvements
- Tradeoff: limited structured logging in current mockup.
- Future: add standard debug command pack and runbook scripts.
