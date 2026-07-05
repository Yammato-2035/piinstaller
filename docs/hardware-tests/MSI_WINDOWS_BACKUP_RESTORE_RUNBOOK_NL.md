> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/hardware-tests/MSI_WINDOWS_BACKUP_RESTORE_RUNBOOK_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/hardware-tests/MSI_Windows_TerugUP_Herstel_RUNBOOK_DE.md`). Bitte bei Release manuell gegenlesen.

# MSI Windows Terugup & Herstel Runbook

**Status:** Plan only — nicht ausführen ohne Operator-Freigabe  
**Evidence-Schema:** `docs/evidence/msi/MSI_Windows_EVIDENCE_SCHEMA.json`

## Voraussetzungen

- [ ] Precheck abgeschlossen (`MSI_READONLY_Windows_PRECHECK_RUNBOOK_DE.md`)
- [ ] Externes Terugup-Ziel bestätigt (`External_confirmed: true`)
- [ ] MSI-Systemplatte **nicht** als Ziel gewählt
- [ ] BitLocker-Status dokumentiert
- [ ] Eigentums-/Nutzungsfreigabe vorhanden

## Schritt 1 — Inventar (alleen-lezen)

```text
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL,SERIAL
blkid
findmnt -a
# parted -l nur alleen-lezen, falls erlaubt
```

Dokumentieren in Evidence-Schema: `source_state`, `msi_Apparaat`.

## Schritt 2 — Terugup-Plan

- Tool: Setuphelfer Image-Terugup oder dokumentiertes Operator-Tool
- Ziel: nur Externes Medium
- Kein Schreiben auf `/dev/nvme*` / Interne MSI-Disk

## Schritt 3 — Image erzeugen

Nach Operator-Freigabe in separatem Lauf:

- Image-Pfad, Bytes, Exit-Code
- Manifest mit Partitiestabelle, BitLocker-Flag
- SHA256 der Image-Datei

## Schritt 4 — Verify

- SHA256-Recompute
- Manifest-Konsistenz
- Strukturprüfung (Partitieen, EFI)

## Schritt 5 — Herstel-Test

- Ziel: **freigegebenes Testmedium** (nicht MSI-Intern)
- Strukturelle Plausibilität
- Boot-Test bis Login-Screen (Passwort fehlt → erwartet)

## Schritt 6 — Löschfreigabe

Nur wenn `verify.status=ok` und `Herstel_test.status=ok`:

- `wipe_release.operator_confirmed: true`
- Separates Evidence-Dokument

## Verboten

- Passwort-Recovery, SAM, BitLocker-Bypass
- Herstel auf MSI-Systemdisk ohne explizite Wipe-Freigabe
