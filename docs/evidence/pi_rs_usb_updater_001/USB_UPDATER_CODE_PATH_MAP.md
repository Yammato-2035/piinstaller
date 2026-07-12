# USB Updater Code Path Map

| Schritt | Datei/Funktion | Eingabe | Schreibziel | Verify | Rollback |
|---------|----------------|---------|-------------|--------|----------|
| CLI parse | `update-fat32-esp-live-payload.sh` | `--target`, `--new-squashfs`, flags | — | usage/die | — |
| Source preflight | `validate_source_payload()` | SquashFS path, expected SHA/version | — | interne Träger, SHA, Symlink | — |
| Target probe | `validate_payload_update_target_probe()` | lsblk/blkid Felder | — | USB, Label, EFI, Serial | — |
| SETUP_LOGS sibling | `validate_sibling_setup_logs_partition()` | logs partition label/fstype | — | Label SETUP_LOGS | — |
| Plan build | `build_payload_update_plan()` | safety + confirm phrase | — | blockers | — |
| Mount ESP | shell `sudo mount` | PART_DEV | MNT | mount ok | umount trap |
| Old state snapshot | `execute_payload_update` | active payload + version.json | evidence dir | SHA old payload | — |
| Temp payload write | shell `cp` | source squashfs | `.sqtmp/filesystem.squashfs.new` | — | rm tmp |
| Temp payload hash | `sha256sum` | temp file | — | vs expected SHA | rm tmp |
| Temp metadata | `build_atomic_esp_version_json`, `build_atomic_esp_evidence_json` | payload version+SHA | mktemp dir | `validate_esp_metadata` | rm meta tmp |
| Prev backup | shell `cp -a` | old payload | `live/filesystem.squashfs.prev-<ver>` | skip if exists | — |
| Payload activate | shell `mv -f` | temp → active | `live/filesystem.squashfs` | SHA after mv | cp from .prev |
| Metadata activate | shell `cp -f` | meta tmp | `setuphelfer/rescue/*.json` | — | restore .prev payload |
| Cleanup staging | shell `rm -rf .sqtmp` | — | — | dir absent | — |
| Final verify | `verify-fat32-esp-rescue-usb.sh` | mount remount | — | expected SHA | — |
| Result JSON | `build_usb_updater_result()` | run state | `usb_update_result.json` | — | — |
