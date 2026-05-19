# Backup e-mail notifications (runtime) – backend, `notification.env`, systemd

Short operations note (no secrets, no passwords in logs).

## `notification.env`

- Typical path: `/etc/setuphelfer/notification.env` (see API field `env_path`).
- Contains SMTP secrets — **never** commit, **never** return in API (`smtp_password_set` only).
- Recommended perms (operator): directory `root:setuphelfer` **0770**, file **0660** (no world-readable, never `777`).

## Backend (`setuphelfer-backend.service`)

- **`NoNewPrivileges=true`:** the backend must **not** run `sudo`. Writes only work with correct Unix permissions and optional systemd **`ReadWritePaths=/etc/setuphelfer`**.
- **No HTTP handler** (notification GET/POST nor `/api/system/status`) may terminate the Uvicorn worker. Failures are **structured JSON** (`status: error`, `diagnosis_id`, …) with **no password** in `message`.
- **SMTP test:** only via the test route (`/api/settings/notifications/email/test`), not implicitly on save.

## Misread as “backend crashed”

- With **`--workers 1`**, long **synchronous** work inside an `async def` route blocks **all** concurrent requests (timeouts while `systemctl` still shows **active**).
- Root cause included `/api/system/status` running expensive `apt` work on the event-loop thread — see evidence `docs/evidence/runtime-results/notification_settings_backend_crash_repair_2026-05-19.json` and fix in `app.py` (`asyncio.to_thread`, simplified update categorisation).

## SMTP / TLS errors

- Treated as **operational** failures (`last_test_status`, `last_test_error_class`), not process crashes.

## Journal

- Full tracebacks: `sudo journalctl -u setuphelfer-backend.service -n 300 --no-pager`
