# Security

## Purpose
Capture the threat model and practical controls for this mockup phase, and prepare for secure production migration.

## Who Should Read This
Technical

## Threat Model
### Inputs
- Resident comment text
- Reaction counts
- Proposal identifiers

### Trust Boundaries
- User-entered UI fields in Streamlit
- Pipeline processing layer
- Local filesystem artifact writes

### Attacker Capabilities
- Submit malformed or abusive text
- Attempt prompt/content injection patterns in free-form comments
- Trigger high-volume submissions to degrade responsiveness

## Key Concepts
- Input validation:
  Practical example: proposal IDs and empty text are validated before pipeline acceptance.
- Offensive content handling:
  Practical example: profanity/toxicity signals are tracked separately to avoid overblocking legitimate critique.
- Artifact safety:
  Practical example: write paths are controlled by artifact contract code, not raw user path input.

## Analogy
Security here is airport screening: validate every passenger (input), isolate restricted zones (contracts), and log checkpoints.

## Key Files and Directories
- src/alpha_app/core/mock_engine.py
- src/alpha_app/core/pipeline.py
- src/alpha_app/core/artifacts.py
- pp.py

## Interfaces and Contracts
- Validation boundary: alidate_event(...).
- Session/auth boundary: lightweight Streamlit login in pp.py (demo only).

## Controls Checklist
- No production secrets committed.
- Input validation on comment payload.
- Deterministic parsing without remote code execution.
- No arbitrary URL fetching from untrusted input in current app path.

## Web/App Risks (Future Production)
- XSS: sanitize/escape user text if rendering in richer frontend stack.
- CSRF/CORS: add standard middleware if moving to browser API backend.
- Session management: replace demo credentials with managed auth provider.
- SSRF: if URL ingestion is introduced, block private IP ranges and enforce allowlists.

## Supply Chain and Dependency Risk
- Dependencies are minimal but should be pinned and scanned in CI.
- Add periodic pip-audit and dependency update checks before production phase.

## Logging and PII Redaction
- Avoid storing raw personal data in logs.
- If resident identifiers are introduced, hash/anonymize before artifact export.

## Failure Modes and Diagnosis
- Unexpected validation bypass: add test around failing input and inspect validation timeline metrics.
- Credential leakage risk: ensure .env remains local and ignored.

## Known Tradeoffs and Future Improvements
- Tradeoff: current authentication is demo-grade.
- Future: enforce production auth, secrets management, audit logging, and policy-based moderation workflows.
