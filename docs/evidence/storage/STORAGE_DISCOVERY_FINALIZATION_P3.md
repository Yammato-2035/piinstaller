# Storage Discovery Finalization P.3

**Kampagne:** A.4 · **Version:** 1.7.15.0

## Vorher / Nachher

| Metrik | Vorher (A.3) | Nachher (A.4) |
|--------|--------------|---------------|
| `app.py` lsblk-Logik inline | Lookup-Helfer ~90 Z. | 0 (nur Wrapper) |
| `app.py` findmnt inline | `_mountpoints_for_disk` | 0 (Wrapper) |
| `app.py` blkid direkt | Clone `_get_fstype` | 1 Callsite → `discover_device_fstype` |

## Migration

Neue APIs in `backend/core/storage_discovery.py`:

- `discover_lsblk_node_by_mountpoint`
- `discover_lsblk_node_by_name`
- `discover_disk_by_name`
- `discover_mountpoints_for_disk`
- `disk_has_system_mount`
- `discover_device_fstype` (+ optional `sudo_runner`)

`app.py` behält Legacy-Wrapper `_lsblk_tree`, `_findmnt_mounts`, `_find_lsblk_by_*` als Delegation.

## Verbleibende Duplikate

- Clone `_clone_disk_info`: lokale `find_node_by_name` (nutzt bereits `_lsblk_tree`/`_findmnt_mounts` Wrapper)
- `duplicate_lsblk_usage_detected` Boundary-Warnung (12) — Aufrufer noch nicht vollständig auf `storage_discovery` umgestellt

## Owner

`storage_discovery` alleiniger Discovery-Owner (read-only).
