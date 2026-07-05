> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/runbooks/MSI_READONLY_WINDOWS_PRECHECK_RUNBOOK_DE.md`). Bitte bei Release manuell gegenlesen.

# MSI Read-only Windows Precheck Runbook

**Modus:** Plan/Contract — in diesem Lauf **nicht ausführen**

## Ziel

Vor jedem Windows-Image-Backup auf dem MSI-Rechner read-only erfassen:

- Devicee-ID / Operator-Label
- `lsblk`, `blkid`, `findmnt`
- Partitionstabelle (read-only: `parted -l` oder äquivalent)
- EFI-, Windows-, NTFS-Erkennung
- BitLocker-Indikator (ohne Entschlüsselung)
- Bootmodus (UEFI/Legacy)
- SMART/Health (falls verfügbar, read-only)
- Zielmedium-Kandidaten (external vs. internal)
- Schreibschutzstatus
- Backup-Zielprüfung
- Risikoampel

## Erlaubte Aktionen (Precheck-Phase)

```json
{
  "scan": true,
  "backup_plan": true,
  "image_backup": false,
  "restore": false,
  "wipe": false,
  "linux_install": false
}
```

## Verboten

- Schreibende Partitionierung
- Mount mit Schreibzugriff auf Windows-Partitionen
- Passwort-/BitLocker-Umgehung
- Credential-Zugriff

## API-Contract

Siehe `docs/api/msi_windows_precheck_contract.yaml` (Stub, keine Runtime in Public Repo).

## Abbruchkriterien

- internales Medium als einziges „Backup-Ziel“ erkannt → `blocked`
- BitLocker `detected_key_missing` → nur strukturelle Evidence, kein Login-Abnahmekriterium
- Unklare Deviceezuordnung → `review_required`
