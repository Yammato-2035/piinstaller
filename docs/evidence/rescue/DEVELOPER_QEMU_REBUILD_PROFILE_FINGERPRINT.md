# Developer QEMU Rebuild — Profile Fingerprint

**Datum:** 2026-06-02  
**Nach:** Prepare `SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu`

## Fingerprint

| Marker | Ergebnis |
|--------|----------|
| Prepared Tree developer-qemu | **yes** (manifest `rescue_build_profile=developer-qemu`) |
| console=ttyS0 | **yes** (`auto/config`) |
| quiet/splash | **nicht aktiv** |
| init=/lib/systemd/systemd | **yes** |
| Autopilot-Hook 090 | **yes** |
| Devserver 10.0.2.2:8001 | **yes** (Autopilot-Unit im Profil-Overlay) |
| Validate Exit 0 | **yes** (nach Prepare; erster Lauf transient Exit 10, Retry OK) |

Log: `developer_qemu_rebuild_profile_fingerprint_latest.log`

## Status

**ready_for_developer_qemu_iso_rebuild_operator_run** — **nur nach** erfolgreichem sudo-Cleanup (sonst LB_EXIT=34).
