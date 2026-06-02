# Rescue ISO Validate — dangerous_path_override Phase 0

**Datum:** 2026-06-02  
**HEAD (vor Fix):** `11453c5`  
**Branch:** `main`  
**Runtime-Profil:** `release`  
**profile_gate_status:** `green`

## Validate-Reproduktion (vor Fix)

| Feld | Wert |
|------|------|
| Validate Exit | **14** |
| Blocker | `dangerous_path_override` |
| Betroffene Datei | `build/rescue/live-build/setuphelfer-rescue-live/config/includes.chroot/etc/systemd/system/setuphelfer-dev-agent.service` |
| Betroffene Zeile | **10** — `Environment=PYTHONPATH=/opt/setuphelfer-rescue` |
| validate_blocker_reproduced | **yes** |

## Kontext

Build-Tree-Cleanup (Dry-Run/Clean/Prepare) war **ok** (root-owned 0, keine Mounts, stale ISO entfernt). Validate scheiterte ausschließlich am DPKG-Preflight-Scan (`validate-live-build-dpkg-preflight.sh`), der `PATH=` als Substring in `PYTHONPATH=` matchte.

Log: `rescue_iso_validate_dangerous_path_repro_latest.log` (Exit 14 vor Fix; nach Fix siehe `rescue_iso_validate_after_dangerous_path_fix_latest.log`).
