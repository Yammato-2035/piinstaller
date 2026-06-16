# R.5A PKFix — ISO Identification

**Datum:** 2026-06-13

## ISO

| Feld | Wert |
|------|------|
| **Pfad** | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| **Größe** | **1,3G** (1 348 468 736 B) |
| **mtime** | 2026-06-13 18:35:45 +0200 |
| **SHA256** | `f94a1c399e345ae297262fb76e01bae0e350b941334a183cd39080dfa4cb9143` |
| **Version** | `1.7.17.0` |
| **Build-Run-ID** | `r5a_rebuild_pkgfix_20260613_163031` |
| **LB_EXIT** | **0** |
| **Profil** | `standard` |

## UEFI Post-Patch

| Feld | Wert |
|------|------|
| Pre-Patch | `validate_exit=34` (isolinux_only, BOOTX64 fehlend) |
| Patch | `patch-rescue-iso-uefi-x64.sh --in-place` → `patch_rc=0` |
| Post-Patch | **`validate_exit=0`** |
| BOOTX64 | **true** |
| SHA256 vor Patch | `54ff2662e75343b05cf18ceae0ae6c2c1cc0e0d857e6ff507c90890dcc9f662d` |
| SHA256 nach Patch | `f94a1c399e345ae297262fb76e01bae0e350b941334a183cd39080dfa4cb9143` |

## Abgrenzung Vorbuild (fehlgeschlagen)

| Build | SHA256 | Status |
|-------|--------|--------|
| `r5a_operator_20260613_153008` (pre-remediation) | `4f511322e0d40e099f318dd959e6758c3404a0bbe80ace4d83a47dc67a77359e` | blocked_missing_runtime_components |
| **PKFix-Build** | `f94a1c399e345ae297262fb76e01bae0e350b941334a183cd39080dfa4cb9143` | **neu** |

## `stat` / `ls`

```
-rw-r--r-- 1 root workspace 1,3G Jun 13 18:35 binary.hybrid.iso
Uid: root  Gid: workspace
```
