# Prompt 02 (Variante Hardware) – Hardware-Testmatrix

> **Master „Prompt 2 – Blocker“:** siehe [`PROMPT_02_BLOCKER_INVENTORY.md`](./PROMPT_02_BLOCKER_INVENTORY.md) und `docs/evidence/release-gates/blocker_inventory.json`.

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
