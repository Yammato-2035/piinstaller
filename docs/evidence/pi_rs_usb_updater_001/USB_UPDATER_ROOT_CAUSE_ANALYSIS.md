# PI-RS-USB-UPDATER-001 — Root Cause Analysis

## Zusammenfassung

Der bisherige FAT32-ESP-Payload-Updater kopierte den SquashFS korrekt, erzeugte ESP-Metadaten aber aus dem **alten Stick-`version.json`**, nicht aus dem neuen Payload. Das führte zu Versionsdrift zwischen aktivem Payload und ESP-Metadaten.

## Driftender Versionsträger

| Träger | Klassifikation | Befund |
|--------|----------------|--------|
| ESP `setuphelfer/rescue/version.json` → `project_version` | **confirmed** | Wurde nach PI-RS-USB-MSI-GUI-002 manuell auf 1.10.0.15 korrigiert; Updater hatte zuvor 1.10.0.13 beibehalten |
| SquashFS-Inhalt vs. ESP-Metadaten | **confirmed** | Stick vor diesem Auftrag: ESP-Metadaten 1.10.0.15, interner Payload `config/version.json` 1.10.0.12 (Drift im alten Payload) |
| Dateiname `filesystem.squashfs.repacked-*` | **strongly_supported** | Wurde nicht als kanonische Quelle geprüft; nur Hash des Quelldatei |

## Bisherige Versionsquelle

**confirmed** — `scripts/rescue-live/update-fat32-esp-live-payload.sh` (vor Fix):

```python
project_version = version_payload.get("project_version", "1.7.9.4")
version_payload["project_version"] = project_version  # bleibt alt
```

Quelle: altes ESP-`version.json` auf dem Stick, nicht der zu kopierende SquashFS.

Evidence: `docs/evidence/pi_rs_usb_msi_gui_002/usb_update_result.json` — Warning:
*"Updater script initially preserved stale project_version in version.json; corrected to 1.10.0.15 post-copy"*

## Ursache der manuellen Nachkorrektur

**confirmed** — Nach dem Update auf 1.10.0.15 blieb `project_version` in ESP-`version.json` auf 1.10.0.13 (gemessen vor Update). Der SquashFS-Hash stimmte, Metadaten nicht. Operator musste `version.json` manuell synchronisieren.

## Warum der Stick vor dem letzten Update 1.10.0.13 statt 1.10.0.14 trug

**strongly_supported** — Brief/Plan nannte 1.10.0.14 als Ziel; tatsächlich gemessene ESP-Metadaten vor PI-RS-USB-MSI-GUI-002: **1.10.0.13** (`usb_update_result.json`). Vermutlich war ein früherer Update-Lauf nicht vollständig in Metadaten reflektiert oder ein zwischenzeitlicher Stand nie auf den Stick geschrieben.

## Risiken

| Risiko | Klassifikation |
|--------|----------------|
| Falsche ESP-Metadaten bei korrektem Payload | **confirmed** |
| Operator-Retest mit falscher erwarteter Version | **confirmed** |
| Falscher interner Payload ohne Source-Preflight | **strongly_supported** (aktueller Stick: interne Carrier-Mismatch 1.10.0.15 vs 1.10.0.12) |
| `.prev-*`-Kette unkontrolliert | **unconfirmed** — historische `.prev-1.10.0.4` bleibt erhalten |

## Exakter Fixpunkt

1. **Source-Preflight** (`validate_source_payload`): SHA256, Symlink, interne Träger `VERSION`, `rescue_payload_version.json`, `config/version.json` aus SquashFS lesen und vergleichen.
2. **ESP-Metadaten** (`build_atomic_esp_version_json` / `build_atomic_esp_evidence_json`): `project_version` und `rescue_payload_version` aus verifiziertem Payload, nie aus altem Stick.
3. **Atomare Reihenfolge**: temp Payload → hash → temp Metadaten → validate → `.prev` backup → atomic activate → sync → final verify.
4. **Rollback** bei Fehler nach Payload-Aktivierung, vor Metadaten-Aktivierung.

## `.prev-*`-Policy

- Maximal eine neue `.prev-<version>` pro Update (aus ESP-Metadaten-Version des alten Payloads).
- Bestehende historische `.prev-1.10.0.4` wird **nicht** gelöscht (kein blindes Aufräumen).
- Neue `.prev-1.10.0.15` wird beim Update angelegt, falls noch nicht vorhanden.
