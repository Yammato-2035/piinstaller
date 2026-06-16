# NTFS/Windows Backup & Restore (Wissen)

**Kurz:** Rettungsstick erkennt Windows/NTFS read-only; Image-Backup/Restore sind separate gated Läufe (F.2–F.4).

## Regeln

- Kein Passwort-/BitLocker-Bypass
- Externes Backup-Ziel Pflicht
- Systemplatte Linux (`nvme1n1` im F.1-Host) niemals als Ziel

## Verweise

- `docs/rescue-stick/RESCUE_STICK_NTFS_WINDOWS_CAPABILITY.md`
- `docs/legal/WINDOWS_BACKUP_PASSWORD_AND_BITLOCKER_POLICY_DE.md`
- `docs/runbooks/MSI_F2_IMAGE_BACKUP_EXECUTION_PROMPT_DRAFT_DE.md`
