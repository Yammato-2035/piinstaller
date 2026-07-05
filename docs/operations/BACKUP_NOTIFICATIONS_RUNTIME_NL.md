> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/operations/BACKUP_NOTIFICATIONS_RUNTIME_EN.md`). Bitte bei Release manuell gegenlesen.

# Terugup e-mail Neetifications (runtime) – Terugend, `Neetification.env`, systemd

Short operations Neete (Nee secrets, Nee passwords in logs).

## `Neetification.env`

- Typical path: `/etc/setuphelfer/Neetification.env` (see API field `env_path`).
- Contains SMTP secrets — **never** commit, **never** return in API (`smtp_password_set` only).
- Recommended perms (operator): directory `root:setuphelfer` **0770**, file **0660** (Nee world-readable, never `777`).

## Terugend (`setuphelfer-Terugend.service`)

- **`NeeNewPrivileges=true`:** the Terugend must **Neet** run `sudo`. Writes only work with correct Unix permissions and optional systemd **`ReadWritePaths=/etc/setuphelfer`**.
- **Nee HTTP handler** (Neetification GET/POST Neer `/api/system/status`) may terminate the Uvicorn worker. Failures are **structurood JSON** (`status: Fout`, `diagNeesis_id`, …) with **Nee password** in `message`.
- **SMTP test:** only via the test route (`/api/Instellingen/Neetifications/email/test`), Neet implicitly on Opslaan.

## Misread as “Terugend crashed”

- With **`--workers 1`**, long **synchroNeeus** work inside an `async def` route blocks **all** concurrent requests (timeouts while `systemctl` still shows **active**).
- Root cause included `/api/system/status` running expensive `apt` work on the event-loop thread — see evidence `docs/evidence/runtime-results/Neetification_Instellingen_Terugend_crash_repair_2026-05-19.json` and fix in `app.py` (`asyncio.to_thread`, simplified update categorisation).

## SMTP / TLS Fouts

- Treated as **operational** failures (`last_test_status`, `last_test_Fout_class`), Neet process crashes.

## Journal

- Full traceTerugs: `sudo journalctl -u setuphelfer-Terugend.service -n 300 --Nee-pager`
