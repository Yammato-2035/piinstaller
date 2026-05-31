# Rescue Dev Agent — QEMU Server URL Fix

**Date:** 2026-05-31
**Commit:** (pending)

## Finding

- QEMU boot smoke: **boot OK**, login OK, `/opt/setuphelfer-rescue` present
- `curl http://127.0.0.1:8000` in guest: **expected failure**

## Fix

| Component | Change |
|-----------|--------|
| `backend/devserver_agent/server_url.py` | Candidate resolution + health probe |
| `backend/devserver_agent/cli.py` | `--resolve-server-url`, `--qemu-host-fallback`, send uses resolved URL |
| `build/rescue/profiles/developer-qemu/` | Explicit 10.0.2.2 + keyboard/remote manifest |
| `scripts/check-dev-agent-rescue-profile-guard.sh` | QEMU profile + remote/keyboard guards |
| `scripts/rescue-live/run-qemu-developer-iso-smoke.sh` | Safe PID path, planned remote flags |

## QEMU host URL

`http://10.0.2.2:8000` under user NAT (local_lab only).

## Remote access (planned, not executed this run)

- VNC `127.0.0.1:1` (local)
- SSH forward disabled by default
- Keyboard `de`, locale `de_DE.UTF-8`, timezone `Europe/Berlin`
- No `0.0.0.0` bind

## PID wrapper fix

Old error: `/qemu_gtk_pid.txt: Keine Berechtigung`
New path: `docs/evidence/runtime-results/rescue/qemu/<RUN_ID>/qemu_gtk_pid.txt`
PID write failure → `WRAPPER_WARNING`, not boot failure.

## Tests

- `test_devserver_agent_server_url_resolution_v1.py`: 10 OK
- Full `test_devserver_agent_*`: 79 OK
- Guard script: exit 0

## QEMU in this run

**Executed** — Host-Ingest-Smoke `qemu_rescue_developer_host_ingest_20260531_120711`: **review_required**.

- Gast-Server-Verbindung fehlgeschlagen (Operator); kein neuer Dev-Server-Report
- ISO noch ohne eingebautes `server_url.py` / `10.0.2.2`-Env
- Host-Backend nur `127.0.0.1:8000` → `network_bind_pending`

Siehe: `docs/evidence/rescue/RESCUE_DEVELOPER_ISO_QEMU_HOST_INGEST_RESULT.md`

## Next step

**FIX DEV SERVER BIND / QEMU HOST PORT REACHABILITY** — dann ISO-Rebuild mit `developer-qemu`-Profil und erneuter Ingest-Smoke.
