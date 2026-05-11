# Evidence — Deploy Rescue live runtime & storage validation

## Nachweisziel

Nachvollziehbare Kette aus Plan-/Ergebnis-JSONs im Handoff-Verzeichnis, API-Routen ohne destruktive Segmente und Unit-Tests, die u. a. read-only-Erzwingung, blockierte interne Evidence-Ziele und fehlenden Auto-SSH-Start prüfen.

## Artefakte

| Artefakt | Ort |
|----------|-----|
| Runner | `backend/deploy/runner_rescue_*.py` (storage, readonly mount, EFI, evidence, remote help, hardware matrix, safety gate) |
| Routen | `backend/deploy/routes.py` |
| Tests | `backend/tests/test_deploy_runner_rescue_*_v1.py` |

## Abnahmehinweis

Erst mit erfolgreicher Live-Abnahme (readonly) und grünen Gates (inkl. Branding/ISO-Readiness) ist ein Release-Bump auf **1.8.0** begründet — siehe Deploy-Doku.
