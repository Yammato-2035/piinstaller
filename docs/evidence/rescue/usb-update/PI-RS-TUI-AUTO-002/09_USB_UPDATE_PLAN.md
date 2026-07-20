# 09 – USB Update Plan

## Updater

`scripts/rescue-live/update-fat32-esp-live-payload.sh` (Plan/Dry-Run bestanden)

| Feld | Wert |
|------|------|
| Zielgerät | `/dev/sda` |
| Partition | `/dev/sda1` SETUPHELFER |
| Modell | Ultra Line |
| Größe | ~59G |
| Buildmodus | payload_repack |
| Aktueller Payload (Squash) | 1.10.0.58 / `3322573de69243be06e363680ddbedebe6462d3badbd45ec6fca62bc8645924a` |
| Neuer Payload | 1.10.0.59 / `3706b824a8992b8abf8d9e20a6d1daa47503cb7c3fada9ac5189e38c2b9ef43e` |
| Quelle SquashFS | Build-Staging Worktree |
| Kernel/Initrd | unverändert (`d8deb726c47f5a690b786c13771e42ee27f82cc3438e88a6ed94a8dd854a9a98` / `385dd4f1395cc4f5e88b4ffa93f6dca883c4698d7f7d04c72db5b6ea99403de8`) |
| Atomic | `.sqtmp/filesystem.squashfs.new → live/filesystem.squashfs` |
| Versionsträger ESP | `setuphelfer/rescue/version.json` + evidence.json |
| Rollback | prev-Backup auf ESP |
| SETUP_LOGS | erkannt, **nicht** beschrieben |
| Partitionstabelle | unverändert |
| `write_allowed` | **true** |
| `payload_update_executed` | false (Plan) |

## Zusätzlich nach Payload-Write (offizielle Lib)

GRUB: `ensure_tui_input_diagnostic_menuentry` auf `boot/grub/grub.cfg`
- Alt: `c8fa330c65659b2db872ab0ea1f6336ee51d0d0e2cc57103d21761a4c6478ef6`
- Neu: `68649d4dab94a19c4ead0acbe060902d215fb36b4b13ffa5ef27d9f195931030`

## Operator-Gates (Auftrag)

1. Exact: `ICH BESTÄTIGE DAS USB-ZIEL /dev/sda`
2. Exact: `USB-UPDATE 1.10.0.59 AUF /dev/sda STARTEN`
3. Updater-Phrase: `UPDATE SETUPHELFER FAT32 ESP LIVE PAYLOAD`
