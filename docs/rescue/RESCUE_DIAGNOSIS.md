# Rescue-Diagnose (Phase 1, Read-only)

## Zweck

Strukturierte **nur lesende** Systemanalyse für den geplanten Rescue-Stick bzw. für den laufenden Setuphelfer-Host. **Kein Restore**, kein Schreiben auf erkannte Systemlaufwerke, kein automatisches **Schreib**-Mount.

## API

- `GET /api/rescue/analyze`
- Antwortmodell: `RescueAnalyzeResponse` (`backend/models/diagnosis.py`) mit `risk_level` (`green` | `yellow` | `red`), `findings[]` (nur **Codes** + `evidence`), `devices`, `boot_status`, `network_status`, `generated_at`.

### Phase 2 – Restore-Dry-Run (Ergänzung)

- `POST /api/rescue/restore-dryrun` — siehe `docs/rescue/RESCUE_DRYRUN.md` und `RESTORE_RISK_MODEL.md`.
- CLI: `python3 scripts/rescue_mode.py --restore-dryrun-backup /pfad/zur/datei.tar.gz`.

## Module

| Modul | Rolle |
|-------|--------|
| `backend/modules/inspect_storage.py` | Blockgeräte (lsblk), blkid, Mount-Status (findmnt, RO/RW), Partitionstabelle (sfdisk/fdisk), UUID-Konflikte, SMART (`smartctl -H`), fsck/xfs_repair nur **-n** und nur wenn **unmounted**. |
| `backend/modules/inspect_boot.py` | `/boot` bzw. `/boot/firmware`, Kernel-/initrd-Namen, `/etc/fstab` grob, optional ESP via `findmnt /boot/efi`. |
| `backend/modules/rescue_readonly_analyze.py` | Orchestrierung, Ampel-Aggregation, Berichte unter `/tmp/setuphelfer-rescue-report.json` und `.md`. |

Wiederverwendung: `storage_detection.detect_block_devices` / `detect_filesystems` / `classify_devices`.

## CLI

```bash
python3 scripts/rescue_mode.py
python3 scripts/rescue_mode.py --json-stdout
```

## i18n

Backend liefert **keine** Nutzerfreitexte für Findings. Übersetzungen: `frontend/src/locales/de.json` und `en.json`, Schlüssel `rescue.<bereich>.<code>.title` / `.user_summary` parallel zum Befund-`code` (z. B. `rescue.storage.duplicate_uuid` → `rescue.storage.duplicate_uuid.title`).

## Sicherheitsgrenzen

- Gemountete Dateisysteme: **kein** `fsck` / `xfs_repair`.
- Unbekannte Geräte: **kein** automatisches Mounten (auch nicht heimlich RW); Mount-„Prüfung“ = Auswertung vorhandener `findmnt`-Daten.
- SMART/fsck können je nach Distribution Root-Rechte benötigen — fehlgeschlagene Aufrufe werden als **yellow** klassifiziert, nicht als Erfolg getarnt.

## Nicht implementiert (Phase 1)

- Analyse **fremder** Root-Dateisysteme per chroot/bind (nur `--root` für fstab/boot-Pfade auf dem **aktuellen** Systemkontext).
- WLAN-Quick-Setup, ISO-Build, automatisches RO-Test-Mount.
- Reparaturmodi (`fsck` ohne `-n`, `xfs_repair` ohne `-n`).

## Tests

- `python3 -m py_compile` auf die neuen Module
- `backend/tests/test_rescue_analyze.py` (API-Shape + UUID-Hilfslogik)
