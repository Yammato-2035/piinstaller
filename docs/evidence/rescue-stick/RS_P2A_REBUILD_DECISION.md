# RS-P2A Rebuild Decision

| Feld | Wert |
|------|------|
| squashfs_update_sufficient | false (allein) |
| grub_esp_update_required | **true** |
| full_usb_rewrite_required | false |

**Begründung:** GRUB-Theme/`grub.cfg` liegen auf FAT32-ESP, nicht im Squashfs. Squashfs-Repack für Backend/GUI/Scripts + separates `update-fat32-esp-grub-branding.sh` + Payload-Update.
