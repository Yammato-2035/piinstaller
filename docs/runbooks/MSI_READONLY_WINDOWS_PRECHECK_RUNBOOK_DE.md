# MSI Read-only Windows Precheck Runbook

**Modus:** Plan/Contract — in diesem Lauf **nicht ausführen**

## Ziel

Vor jedem Windows-Image-Backup auf dem MSI-Rechner read-only erfassen:

- Geräte-ID / Operator-Label
- `lsblk`, `blkid`, `findmnt`
- Partitionstabelle (read-only: `parted -l` oder äquivalent)
- EFI-, Windows-, NTFS-Erkennung
- BitLocker-Indikator (ohne Entschlüsselung)
- Bootmodus (UEFI/Legacy)
- SMART/Health (falls verfügbar, read-only)
- Zielmedium-Kandidaten (extern vs. intern)
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

- Internes Medium als einziges „Backup-Ziel“ erkannt → `blocked`
- BitLocker `detected_key_missing` → nur strukturelle Evidence, kein Login-Abnahmekriterium
- Unklare Gerätezuordnung → `review_required`
