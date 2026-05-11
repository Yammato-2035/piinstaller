# Laptop Failure Test Chain (Recovery)

Ziel: **reale** Laptop-Recovery-Tests (Backup → Verify → Restore-Preview → Runtime-Handoffs) ohne künstliche Erfolgsmeldungen.

## Kette (Operator-Reihenfolge)

1. Backup lokalisieren (List-API oder Mount-Nachweis).
2. Verify **basic** (`POST /api/backup/verify`, erlaubter Pfad).
3. Verify **deep** (nur mit freigegebenem Archiv).
4. Restore **Preview** (`POST /api/backup/restore`, `mode=preview`) — niemals Execute ohne separates Gate.
5. Runtime Result Template (`POST /api/deploy/runner/manual-runtime/result-template`).
6. Runtime Result Validator / Handoff-Dryruns (Deploy-Runner, Evidence unter `docs/evidence/runtime-results/handoff/`).
7. Evidence-Ingestion (strukturierte JSONs, Timeline/Summary).
8. Final Summary / Report (`laptop-failure-final-report` etc.).

## Final Readiness Gate

- Runner: `backend/deploy/runner_laptop_failure_test_execution_readiness_final_gate.py`
- API: `POST /api/deploy/runner/manual-runtime/laptop-failure-test-execution-readiness-final-gate`
- Handoff: `docs/evidence/runtime-results/handoff/laptop_failure_test_execution_readiness_gate.json`
- Reports: `docs/evidence/LAPTOP_FAILURE_TEST_READINESS_REPORT_{DE,EN}.md` (werden beim Gate-Lauf aktualisiert)

**Parameter:** `probe_live_system` (default false) — ohne Live-Probe keine grünen API-/Storage-Aussagen.

## STRICT

Kein Restore-Execute, kein Low-Level-Block-Write durch den Gate-Runner. Blocker und Ampeln nur evidenzbasiert.
