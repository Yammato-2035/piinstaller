# Evidence — DEPLOY_RESCUE_PSEUDO_BOOT_INTEGRATION

## Nachweisziel

Dokumentieren, dass die Pseudo-Boot-Integration **nur** JSON unter `build/rescue/` und Handoffs unter `docs/evidence/runtime-results/handoff/` schreibt und **keine** VM-, QEMU-, ISO- oder `systemctl`-Ausführung auslöst.

## Pflicht-Tests

`backend/tests/test_deploy_runner_rescue_pseudo_boot_integration_v1.py` plus Regression (Rescue-Artefakt, ISO-Readiness-Pipeline, Branding-Guard).

## Operator

Nach erfolgreicher Kette Handoff-JSONs versionieren; Versionshinweis siehe Deploy-DE-Doku.
