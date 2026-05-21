# Rescue Offline Backup Orchestrator (Phase C.2)

**Stand:** 2026-05-20  
**Modul:** `backend/rescue/backup_orchestrator.py` → `build_rescue_offline_backup_plan()`

---

## Zweck

Erzeugt einen **Plan** für Offline-BR-001; startet **niemals** Backup, `tar`, `systemd-run`, `systemd-inhibit` oder Verify.

## Eingaben

- `boot_context` (oder automatisch via `build_rescue_boot_context`)
- `source_root`, `target_path`
- `backup_profile_id` (Default: `offline-full`)
- Optional `storage_snapshot` für externe Zielklassifikation

## Blocker

- Fehlende `source_root` / `target_path`
- Ziel unter `source_root`
- Systemkritisches internes Ziel (`/`, `/boot`, …)
- Profil unbekannt
- Profil verlangt externes Ziel, Klassifikation fehlt

## Plan-Felder (Auszug)

- `runner`: `backend.tools.backup_runner` (Referenz only)
- `execution_allowed`: **immer false**
- `requires_operator_confirmation`: true
- `expected_excludes`, Manifest/SHA256-Flags aus Profil

## API (Plan only)

`POST /api/deploy/rescue/offline-backup-plan`  
Codes: `DEPLOY_RESCUE_OFFLINE_BACKUP_PLAN_{READY|REVIEW_REQUIRED|BLOCKED}`

**Nicht** vorhanden: `execute`, `backup/start`, `mount`, `iso/build`.

## Nächster Schritt

Phase C.4: Restore-Preview-Handoff oder Phase B.3: `app.py` target-check-Adapter.
