# USB update plan (dry-run)

Updater: `scripts/rescue-live/update-fat32-esp-live-payload.sh`

| Field | Value |
|-------|-------|
| Target | /dev/sda → /dev/sda1 SETUPHELFER |
| Model | Ultra Line |
| Current | 1.10.0.59 / `3706b824a8992b8abf8d9e20a6d1daa47503cb7c3fada9ac5189e38c2b9ef43e` |
| New | 1.10.0.60 / `ee17958c8667c4020add87ef87b5041e6b20f4e709645bbc2846a47f9164270c` |
| Source squashfs | build staging worktree |
| Kernel/Initrd | unchanged |
| Atomic | `.sqtmp/filesystem.squashfs.new → live/filesystem.squashfs` |
| SETUP_LOGS | detected, not written |
| write_allowed | **true** |
| payload_update_executed | false (plan) |

Operator confirmations required by task:
1. `ICH BESTÄTIGE DAS USB-ZIEL /dev/sda`
2. `USB-UPDATE 1.10.0.60 AUF /dev/sda STARTEN`
3. Updater phrase: `UPDATE SETUPHELFER FAT32 ESP LIVE PAYLOAD`
