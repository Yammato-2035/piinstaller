# F.1 MSI Windows Read-only Precheck Result

**Run-ID:** F1-MSI-WINDOWS-READONLY-PRECHECK  
**Status:** **GREEN** (read-only, Quelle eindeutig)

## Ergebnis

| Prüfung | Wert |
|---------|------|
| msi_source_status | `identified` |
| source_device | `/dev/nvme0n1` |
| windows_detected | ja |
| efi_detected | ja |
| ntfs_detected | ja |
| bitlocker_status | `not_detected` |
| backup_target | `/dev/sda` (USB ext4, extern) |
| recommended_next_step | `MSI_IMAGE_BACKUP` (F.2) |

## Erlaubte nächste Aktionen (F.1)

| Aktion | Erlaubt |
|--------|---------|
| scan | ja |
| image_backup_plan | **ja** |
| image_backup_execute | **nein** |
| verify / restore / wipe / linux_install | **nein** |

## Policy-Bestätigung

- Kein Mount auf NTFS-Partitionen
- Kein Passwort-/BitLocker-Bypass
- Windows-Login kein Abnahmekriterium (Passwort fehlt)

JSON: `F1_MSI_WINDOWS_READONLY_PRECHECK_RESULT.json`
