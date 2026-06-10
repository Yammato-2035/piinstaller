# RS-001 FAT32 ESP Payload Update — 1.7.11.0

**Datum:** 2026-06-10  
**Version:** `1.7.11.0`  
**Status:** **success** (udisksctl rw Operator-Fallback)

## SquashFS

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/filesystem.squashfs.repacked-1.7.11.0` |
| `new_squashfs_sha256` | `a3e58964ffffe032fd7e543e5e28bd64156981347647a0ba9208101cb9d7726d` |
| `old_stick_sha256` | `0b303d3ab563f4aeaa354813dcbf46e8fb934a3f23d4705251129f80f2ac51dc` |

## Payload-Update

| Feld | Wert |
|------|------|
| `payload_update_status` | **success** |
| `verify_status` | **success** |
| `stick_squashfs_hash_ok` | **true** |
| `staging_artifacts_cleaned` | **true** |
| Methode | udisksctl rw + atomisches `.sqtmp` → `live/filesystem.squashfs` |
| Hinweis | `update-fat32-esp-live-payload.sh --execute-update` benötigt passwordless sudo; Plan-only bestanden |

Evidence: `docs/evidence/runtime-results/rescue/fat32_esp_payload_update_20260610_040*/`

## RS-001

```text
Stick Acceptance: ok
Hardware Retest Allowed: true
RS-001: yellow (HW Level 6 ausstehend)
```
