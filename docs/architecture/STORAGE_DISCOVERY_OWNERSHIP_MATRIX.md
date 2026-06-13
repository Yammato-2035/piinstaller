# Storage Discovery Ownership Matrix (P.1)

| Datei | Funktion | Zweck | Künftig Canonical API |
|-------|----------|-------|----------------------|
| backend/modules/storage_detection.py | detect_block_devices | lsblk -J | `discover_block_devices` |
| backend/modules/storage_detection.py | detect_filesystems | blkid | `discover_filesystems` |
| backend/modules/storage_detection.py | _findmnt_json_for_path | findmnt -J | `discover_mounts` |
| backend/core/mount_facade.py | build_mount_inventory_snapshot | findmnt -J -R | `discover_mounts` |
| backend/core/storage_discovery.py | discover_* | delegation | `canonical API` |
| backend/core/storage_facade.py | get_storage_inventory | via discovery | `discover_block_devices / discover_filesystems` |
| backend/app.py | _lsblk_tree | lsblk | `discover_block_devices — **offen**` |
| backend/app.py | _findmnt_mounts | findmnt | `discover_mounts — **offen**` |
| backend/app.py | blkid helpers ~11683 | blkid | `discover_filesystems — **offen**` |
| backend/core/safe_device.py | resolve_mount_source_for_path | findmnt | `bleibt Safety-Owner` |

Vollständiges Inventar: `STORAGE_DISCOVERY_AUDIT_P1.md`
