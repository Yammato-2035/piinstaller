# Rescue ISO — Successful Hybrid Build Log Classification

**Klassifikation:** `build_succeeded_artifact_present_zsync_stale_after_iso`  
**Diagnosecode:** `RESCUE-BUILD-ZSYNC-STALE-001`

| Signal | Erwartet | Ist |
|--------|----------|-----|
| `isohybrid: not found` erneut | nein | nein |
| rsvg-Fehler erneut | nein | nein |
| bootlogo-Fehler erneut | nein | nein |
| chroot/proc-Cleanup erneut | nein | nein |
| zsync stale | ja (wenn `.zsync.xz` existierte) | ja |
| `LB_EXIT` | 1 nach ISO | 1 |
| ISO vor Fehler | ja | ja (`extents written`, hybrid ISO auf Disk) |

**zsync-Fehler:** `xz: binary.hybrid.iso.zsync.xz: Die Datei existiert bereits`

JSON: `rescue_iso_successful_hybrid_build_log_classification_latest.json`
