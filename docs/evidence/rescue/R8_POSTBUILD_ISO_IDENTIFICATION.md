# R.8 — Post-Build ISO Identification

**Datum:** 2026-06-13  
**Build-Run:** `r8_clean_20260613_201824`

## ISO

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| Größe | **1 348 468 736** Bytes (~1,3 GiB) |
| mtime | **2026-06-13 22:23:43** (+0200) |
| SHA256 | **`18d613e569da4b322f962a1928054d5660280a7ab9626302d2100d3150760390`** |

## Vorheriges ISO (pre-R.6 Build)

| Feld | Wert |
|------|------|
| SHA256 | `f94a1c399e345ae297262fb76e01bae0e350b941334a183cd39080dfa4cb9143` |
| mtime | 2026-06-13 18:35 |

**ISO ist neu** (SHA256 und mtime geändert).

## Build

| Feld | Wert |
|------|------|
| **LB_EXIT** | **0** |
| `run_id` | `r8_clean_20260613_201824` |
| Profil | `standard` |
| Build-Zeit | 2026-06-13 22:18:24 → 22:23:39 (~5 min) |

## UEFI Post-Patch

| Feld | Wert |
|------|------|
| Pre-patch validate | Exit 34 (isolinux_only, EFI fehlend) |
| Patch | `patch-rescue-iso-uefi-x64.sh --in-place` — **OK** |
| Post-patch `validate_exit` | **0** |
| `BOOTX64.EFI` | **ja** |
| SHA256 nach Patch | `18d613e569da4b322f962a1928054d5660280a7ab9626302d2100d3150760390` |
