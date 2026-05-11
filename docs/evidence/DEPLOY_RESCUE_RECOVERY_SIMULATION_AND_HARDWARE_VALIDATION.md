# Evidence — Deploy Rescue recovery simulation & hardware validation

## Nachweisziel

Runner unter `backend/deploy/runner_rescue_recovery_*.py`, Handoffs unter `docs/evidence/runtime-results/handoff/`, API-Routen in `backend/deploy/routes.py`, Unit-Tests `backend/tests/test_deploy_runner_rescue_recovery_*_v1.py`.

## Kernaussagen

- Restore nur als **Preview**; `writes_executed` bleibt false.
- Backup-Verify nutzt Manifest + SHA256 nur innerhalb des konfigurierten `build/rescue/…`-Scanroots.
- Final Gate bindet Zielvalidierung, Verify, Preview, Hardware-Kette und Live-Runtime-Safety-Gate.
