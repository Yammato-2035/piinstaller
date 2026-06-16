# MSI Windows Backup & Restore Runbook

**Status:** Plan only — nicht ausführen ohne Operator-Freigabe  
**Evidence-Schema:** `docs/evidence/msi/MSI_WINDOWS_EVIDENCE_SCHEMA.json`

## Voraussetzungen

- [ ] Precheck abgeschlossen (`MSI_READONLY_WINDOWS_PRECHECK_RUNBOOK_DE.md`)
- [ ] Externes Backup-Ziel bestätigt (`external_confirmed: true`)
- [ ] MSI-Systemplatte **nicht** als Ziel gewählt
- [ ] BitLocker-Status dokumentiert
- [ ] Eigentums-/Nutzungsfreigabe vorhanden

## Schritt 1 — Inventar (read-only)

```text
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL,SERIAL
blkid
findmnt -a
# parted -l nur read-only, falls erlaubt
```

Dokumentieren in Evidence-Schema: `source_state`, `msi_device`.

## Schritt 2 — Backup-Plan

- Tool: Setuphelfer Image-Backup oder dokumentiertes Operator-Tool
- Ziel: nur externes Medium
- Kein Schreiben auf `/dev/nvme*` / interne MSI-Disk

## Schritt 3 — Image erzeugen

Nach Operator-Freigabe in separatem Lauf:

- Image-Pfad, Bytes, Exit-Code
- Manifest mit Partitionstabelle, BitLocker-Flag
- SHA256 der Image-Datei

## Schritt 4 — Verify

- SHA256-Recompute
- Manifest-Konsistenz
- Strukturprüfung (Partitionen, EFI)

## Schritt 5 — Restore-Test

- Ziel: **freigegebenes Testmedium** (nicht MSI-Intern)
- Strukturelle Plausibilität
- Boot-Test bis Login-Screen (Passwort fehlt → erwartet)

## Schritt 6 — Löschfreigabe

Nur wenn `verify.status=ok` und `restore_test.status=ok`:

- `wipe_release.operator_confirmed: true`
- Separates Evidence-Dokument

## Verboten

- Passwort-Recovery, SAM, BitLocker-Bypass
- Restore auf MSI-Systemdisk ohne explizite Wipe-Freigabe
