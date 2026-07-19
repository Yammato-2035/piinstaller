# Disk Role Map — MSI RS-011B (ausfüllen)

| device | role | can_be_backup_source | can_be_backup_target | notes |
|--------|------|---------------------|---------------------|-------|
| /dev/nvme*n* | windows_system_disk | | | interne Windows-Quelle |
| /dev/sd* (USB stick) | rescue_usb_stick | | | Boot, kein Ziel |
| SETUP_LOGS | setup_logs | | | Evidence, kein Ziel |
| /dev/sd* (extern) | backup_target | | | externes Ziel |

## Fehlercode (einer)

- [ ] MSI_SOURCE_SELECTION_OK
- [ ] MSI_BACKUP_SOURCE_SELECTOR_EMPTY
- [ ] MSI_WINDOWS_DISK_NOT_CLASSIFIED
- [ ] MSI_NVME_VISIBLE_BUT_FILTERED
- [ ] MSI_TARGET_FILTER_FAILED
- [ ] MSI_RESCUE_STICK_VISIBLE_AS_TARGET
- [ ] MSI_SETUP_LOGS_VISIBLE_AS_TARGET
