# Prompt 02 (Variante Hardware) – Hardware-Testmatrix

> **Master „Prompt 2 – Blocker“:** siehe [`PROMPT_02_BLOCKER_INVENTORY.md`](./PROMPT_02_BLOCKER_INVENTORY.md) und `docs/evidence/release-gates/blocker_inventory.json`.

## PHASE 0 – Mandatory Runtime Version Gate (Pflicht)

1. `./scripts/check-runtime-deploy-gate.sh` (Exit **0**), falls vorhanden; sonst `./scripts/check-backend-version-gate.sh` plus `GET /api/dev-dashboard/status` (`deploy_drift`) manuell.
2. Bei Exit **≠ 0**: **STOP** — keine Hardwaretest-Ausführung dokumentieren; **`blocked_runtime_outdated`**; `docs/developer/CURSOR_WORK_RULES.md`.

STRICT MODE – HARDWARE TEST MATRIX PREP

ZIEL:
Erzeuge/aktualisiere die Hardwaretestmatrix, ohne Hardwaretests auszuführen.

NICHT ERLAUBT:
- keine echten Systemänderungen
- kein Restore
- kein Mount
- kein sudo
- kein Schreiben auf Datenträger

PHASE 1 – MATRIX: `docs/testing/HARDWARE_TEST_MATRIX.md`

PHASE 2 – GERÄTEKLASSEN: Pi 5 SD/NVMe, USB-SSD, Stick, Laptop UEFI, Dualboot, SD langsam.

PHASE 3 – TESTARTEN: Backup, Verify, Restore Preview, Restore externes Ziel, Safety No-Write, Boot, Service.

PHASE 4 – EVIDENCE: Templates unter `docs/evidence/hardware/HW-*.json`

ABSCHLUSSBERICHT: Geräte, Testfälle, Risiken, offene Hardware, nächste echte Tests.
