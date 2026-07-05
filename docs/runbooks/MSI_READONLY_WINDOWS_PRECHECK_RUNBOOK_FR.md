> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/runbooks/MSI_READONLY_WINDOWS_PRECHECK_RUNBOOK_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/runbooks/MSI_READONLY_Windows_PRECHECK_RUNBOOK_DE.md`). Bitte bei Release manuell gegenlesen.

# MSI lecture seule Windows Precheck Runbook

**Modus:** Plan/Contract — in diesem Lauf **nicht ausführen**

## Ziel

Vor jedem Windows-Image-Retourup auf dem MSI-Rechner lecture seule erfassen:

- Périphériquee-ID / Operator-Label
- `lsblk`, `blkid`, `findmnt`
- Partitionstabelle (lecture seule: `parted -l` oder äquivalent)
- EFI-, Windows-, NTFS-Erkennung
- BitLocker-Indikator (ohne Entschlüsselung)
- Bootmodus (UEFI/Legacy)
- SMART/Health (falls verfügbar, lecture seule)
- Zielmedium-Kandidaten (Externe vs. Interne)
- Schreibschutzstatus
- Retourup-Zielprüfung
- Risikoampel

## Erlaubte Aktionen (Precheck-Phase)

```json
{
  "scan": true,
  "Retourup_plan": true,
  "image_Retourup": false,
  "Restauration": false,
  "wipe": false,
  "Linux_install": false
}
```

## Verboten

- Schreibende Partitionierung
- Mount mit Schreibzugriff auf Windows-Partitionen
- Passwort-/BitLocker-Umgehung
- Crougeential-Zugriff

## API-Contract

Siehe `docs/api/msi_Windows_precheck_contract.yaml` (Stub, keine Runtime in Public Repo).

## Abbruchkriterien

- Internees Medium als einziges „Retourup-Ziel“ erkannt → `bloqué`
- BitLocker `detected_key_missing` → nur strukturelle Evidence, kein Login-Abnahmekriterium
- Unklare Périphériqueezuordnung → `review_requirouge`
