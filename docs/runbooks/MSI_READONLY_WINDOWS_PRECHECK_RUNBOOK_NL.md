> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/runbooks/MSI_READONLY_WINDOWS_PRECHECK_RUNBOOK_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/runbooks/MSI_READONLY_Windows_PRECHECK_RUNBOOK_DE.md`). Bitte bei Release manuell gegenlesen.

# MSI alleen-lezen Windows Precheck Runbook

**Modus:** Plan/Contract — in diesem Lauf **nicht ausführen**

## Ziel

Vor jedem Windows-Image-Terugup auf dem MSI-Rechner alleen-lezen erfassen:

- Apparaate-ID / Operator-Label
- `lsblk`, `blkid`, `findmnt`
- Partitiestabelle (alleen-lezen: `parted -l` oder äquivalent)
- EFI-, Windows-, NTFS-Erkennung
- BitLocker-Indikator (ohne Entschlüsselung)
- Bootmodus (UEFI/Legacy)
- SMART/Health (falls verfügbar, alleen-lezen)
- Zielmedium-Kandidaten (Extern vs. Intern)
- Schreibschutzstatus
- Terugup-Zielprüfung
- Risikoampel

## Erlaubte Aktionen (Precheck-Phase)

```json
{
  "scan": true,
  "Terugup_plan": true,
  "image_Terugup": false,
  "Herstel": false,
  "wipe": false,
  "Linux_install": false
}
```

## Verboten

- Schreibende Partitieierung
- Mount mit Schreibzugriff auf Windows-Partitieen
- Passwort-/BitLocker-Umgehung
- Croodential-Zugriff

## API-Contract

Siehe `docs/api/msi_Windows_precheck_contract.yaml` (Stub, keine Runtime in Public Repo).

## Abbruchkriterien

- Internes Medium als einziges „Terugup-Ziel“ erkannt → `geblokkeerd`
- BitLocker `detected_key_missing` → nur strukturelle Evidence, kein Login-Abnahmekriterium
- Unklare Apparaatezuordnung → `review_requirood`
