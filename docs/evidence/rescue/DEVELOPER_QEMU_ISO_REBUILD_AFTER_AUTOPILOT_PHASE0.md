# Developer QEMU ISO Rebuild After Autopilot Fix — Phase 0

**Datum:** 2026-06-03  
**HEAD:** `fa9d2b0`  
**Branch:** `main`

## Runtime

| Feld | Wert |
|------|------|
| `install_profile` | release |
| `profile_gate_status` | green |

## Autopilot-Fix

| Feld | Wert |
|------|------|
| Fix-Commit | `fa9d2b0` |
| Autopilot-Fix vorhanden | **yes** |
| Readiness vor Build | `ready_for_developer_qemu_iso_rebuild_operator_run` |

## Auftragsgrenzen

| | |
|---|---|
| Build in diesem Lauf erlaubt | **yes** (Policy: Operator-Terminal + sudo) |
| QEMU | **no** |
| USB | **no** |

## Ist-Zustand vor Operator-Rebuild

| | |
|---|---|
| ISO auf Disk | SHA `3ee02b36…` (Build **vor** Wants-Fix im Squashfs) |
| Squashfs-Validator | Exit **12** (Autopilot wants fehlt) |
| Agent-Build-Versuch | Exit **30** (kein TTY/sudo) |
