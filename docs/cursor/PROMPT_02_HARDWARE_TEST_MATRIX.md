# Prompt 02 (Variante Hardware) – Hardware-Testmatrix

> **Master „Prompt 2 – Blocker“:** siehe [`PROMPT_02_BLOCKER_INVENTORY.md`](./PROMPT_02_BLOCKER_INVENTORY.md) und `docs/evidence/release-gates/blocker_inventory.json`.

## PHASE 0 – BACKEND VERSION GATE (Pflicht)

`scripts/check-backend-version-gate.sh`, `curl -i http://127.0.0.1:8000/api/version`, `systemctl status setuphelfer-backend.service` — bei Nicht-Grün: **keine** Hardwaretest-Ausführung dokumentieren; zuerst Update-Gate (`docs/operations/BACKEND_VERSION_UPDATE_GATE_DE.md`).

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
