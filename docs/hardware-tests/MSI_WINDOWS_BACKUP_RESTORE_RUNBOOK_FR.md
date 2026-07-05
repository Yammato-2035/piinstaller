> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/hardware-tests/MSI_WINDOWS_BACKUP_RESTORE_RUNBOOK_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/hardware-tests/MSI_Windows_RetourUP_Restauration_RUNBOOK_DE.md`). Bitte bei Release manuell gegenlesen.

# MSI Windows Retourup & Restauration Runbook

**Status:** Plan only — nicht ausführen ohne Operator-Freigabe  
**Evidence-Schema:** `docs/evidence/msi/MSI_Windows_EVIDENCE_SCHEMA.json`

## Voraussetzungen

- [ ] Precheck abgeschlossen (`MSI_READONLY_Windows_PRECHECK_RUNBOOK_DE.md`)
- [ ] Externees Retourup-Ziel bestätigt (`Externeal_confirmed: true`)
- [ ] MSI-Systemplatte **nicht** als Ziel gewählt
- [ ] BitLocker-Status dokumentiert
- [ ] Eigentums-/Nutzungsfreigabe vorhanden

## Schritt 1 — Inventar (lecture seule)

```text
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL,SERIAL
blkid
findmnt -a
# parted -l nur lecture seule, falls erlaubt
```

Dokumentieren in Evidence-Schema: `source_state`, `msi_Périphérique`.

## Schritt 2 — Retourup-Plan

- Tool: Setuphelfer Image-Retourup oder dokumentiertes Operator-Tool
- Ziel: nur Externees Medium
- Kein Schreiben auf `/dev/nvme*` / Internee MSI-Disk

## Schritt 3 — Image erzeugen

Nach Operator-Freigabe in separatem Lauf:

- Image-Pfad, Bytes, Exit-Code
- Manifest mit Partitionstabelle, BitLocker-Flag
- SHA256 der Image-Datei

## Schritt 4 — Verify

- SHA256-Recompute
- Manifest-Konsistenz
- Strukturprüfung (Partitionen, EFI)

## Schritt 5 — Restauration-Test

- Ziel: **freigegebenes Testmedium** (nicht MSI-Interne)
- Strukturelle Plausibilität
- Boot-Test bis Login-Screen (Passwort fehlt → erwartet)

## Schritt 6 — Löschfreigabe

Nur wenn `verify.status=ok` und `Restauration_test.status=ok`:

- `wipe_release.operator_confirmed: true`
- Separates Evidence-Dokument

## Verboten

- Passwort-Recovery, SAM, BitLocker-Bypass
- Restauration auf MSI-Systemdisk ohne explizite Wipe-Freigabe
