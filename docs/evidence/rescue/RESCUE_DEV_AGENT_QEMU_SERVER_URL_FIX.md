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

**Not executed** (code/plan only).

## Next step

**RESCUE DEVELOPER ISO QEMU BOOT SMOKE WITH HOST DEV SERVER INGEST**

Use developer-qemu env or `--qemu-host-fallback` and verify `curl http://10.0.2.2:8000/api/dev-server/health` in guest.
