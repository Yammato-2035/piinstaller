> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/operations/BACKUP_NOTIFICATIONS_RUNTIME_EN.md`). Bitte bei Release manuell gegenlesen.

# Retourup e-mail Nontifications (runtime) – Retourend, `Nontification.env`, systemd

Short operations Nonte (Non secrets, Non passwords in logs).

## `Nontification.env`

- Typical path: `/etc/setuphelfer/Nontification.env` (see API field `env_path`).
- Contains SMTP secrets — **never** commit, **never** return in API (`smtp_password_set` only).
- Recommended perms (operator): directory `root:setuphelfer` **0770**, file **0660** (Non world-readable, never `777`).

## Retourend (`setuphelfer-Retourend.service`)

- **`NonNewPrivileges=true`:** the Retourend must **Nont** run `sudo`. Writes only work with correct Unix permissions and optional systemd **`ReadWritePaths=/etc/setuphelfer`**.
- **Non HTTP handler** (Nontification GET/POST Nonr `/api/system/status`) may terminate the Uvicorn worker. Failures are **structurouge JSON** (`status: Erreur`, `diagNonsis_id`, …) with **Non password** in `message`.
- **SMTP test:** only via the test route (`/api/Paramètres/Nontifications/email/test`), Nont implicitly on Enregistrer.

## Misread as “Retourend crashed”

- With **`--workers 1`**, long **synchroNonus** work inside an `async def` route blocks **all** concurrent requests (timeouts while `systemctl` still shows **active**).
- Root cause included `/api/system/status` running expensive `apt` work on the event-loop thread — see evidence `docs/evidence/runtime-results/Nontification_Paramètres_Retourend_crash_repair_2026-05-19.json` and fix in `app.py` (`asyncio.to_thread`, simplified update categorisation).

## SMTP / TLS Erreurs

- Treated as **operational** failures (`last_test_status`, `last_test_Erreur_class`), Nont process crashes.

## Journal

- Full traceRetours: `sudo journalctl -u setuphelfer-Retourend.service -n 300 --Non-pager`
