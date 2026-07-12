# PI-RS-USB-UPDATER-001 — Ergebnis

## Vorheriger Stickzustand

| Feld | Wert |
|------|------|
| ESP-Metadaten `project_version` | 1.10.0.15 |
| Aktiver Payload-SHA256 | `307ae9a381e2792fddd2ca8ebb6c20550544f0b167e2461c323c596651ecd318` |
| Interne Carrier im alten Payload | VERSION/rescue 1.10.0.15, config/version.json **1.10.0.12** (Drift) |
| `.prev-*` | `filesystem.squashfs.prev-1.10.0.4` |
| SETUP_LOGS | 964 Dateien, unverändert |

## Root Cause Metadatendrift

Der alte Updater übernahm `project_version` aus dem **alten ESP-`version.json`**, nicht aus dem neuen SquashFS. Nach PI-RS-USB-MSI-GUI-002 war manuelle Korrektur auf 1.10.0.15 nötig.

## Updater-Änderungen

- Neues Modul `backend/core/rescue_usb_payload_atomic_update.py`
- Source-Preflight: SHA256, interne Versionsträger, Dateiname vs. Inhalt
- ESP-Metadaten deterministisch aus Payload-Version (`build_atomic_esp_version_json`)
- Atomare Reihenfolge: temp → hash → metadata → mv prev → activate → verify
- Rollback bei Fehler nach Payload-Aktivierung
- `.prev-*`-Policy: mv statt cp, max-one-prev, incomplete cleanup
- `/dev/disk/by-id/` Partition-Pfad-Fix in `partition_path_for_target`
- Strukturiertes Ergebnis-JSON

## Kanonische Versionsquelle

SquashFS-Inhalt (`VERSION`, `config/rescue_payload_version.json`, `config/version.json`) — siehe `docs/architecture/RESCUE_USB_PAYLOAD_UPDATE_CONTRACT.md`.

## Physisches Update

- Gerät: Intenso Ultra Line via `/dev/disk/by-id/usb-Intenso_Ultra_Line_24111412110686-0:0`
- Runtime-Evidence: `docs/evidence/runtime-results/rescue/fat32_esp_payload_update_20260712_202320`
- Erster Versuch blockiert durch vollen ESP (cp-Backup); Recovery und erfolgreicher zweiter Lauf

## Finaler Zustand

| Prüfung | Ergebnis |
|---------|----------|
| Payload-SHA256 | `cada647ccc11a545a8b4eb6f42deb8745bdedcd5b1662e738c96d68c987621b5` |
| VERSION | 1.10.0.16 |
| rescue_payload_version.json | 1.10.0.16 |
| config/version.json | 1.10.0.16 |
| ESP project_version | 1.10.0.16 |
| ESP rescue_payload_version | 1.10.0.16 |
| content_verified | true |
| Manuelle Metadatenkorrektur | **nein** |
| Partitionstabelle | unverändert |
| SETUP_LOGS | unverändert |
| `.prev-*` | `filesystem.squashfs.prev-1.10.0.15` |

## Tests

- `backend/tests/test_rescue_usb_payload_updater_v1.py`: 14 passed
- MSI/FAT32-Regression: 43 passed
- Source Content/Secret-Gate: grün

## Zielaussage

Der Setuphelfer-Rettungsstick trägt den unveränderten und verifizierten Payload **1.10.0.16**. SquashFS, ESP-Metadaten und alle aktiven Versionsträger sind konsistent. Das Update erforderte **keine** manuelle Metadatenkorrektur.

**Nächster Auftrag:** PI-RS-MSI-RETEST-003 (physischer MSI-Boot)
