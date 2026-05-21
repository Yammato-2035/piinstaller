# Rescue Restore Preview Handoff (Phase C.4)

**Stand:** 2026-05-20  
**Modul:** `backend/rescue/restore_preview_orchestrator.py` → `build_rescue_restore_preview_plan()`

---

## Zweck

Vorbereitung einer **Restore-Vorschau** auf dem Rettungsstick — **keine Wiederherstellung**.

- Boot-Kontext lesen (`rescue/boot_context.py`)
- Storage-/Mount-Snapshots optional einbeziehen
- Archiv + Manifest + Ziel referenzieren
- Backup-before-overwrite-Gate (`core/backup_before_write_gate.py`)
- Kanonische Module **nur referenzieren**:
  - Restore-Preview: `modules.rescue_restore_dryrun.run_restore_dryrun_pipeline`
  - Verify: `modules.backup_verify` (`verify_basic`, `verify_deep`)

## Profil

`offline-full-restore-preview` in `core/restore_profiles.py` — `execution_allowed: false`.

## API (Plan only)

`POST /api/deploy/rescue/restore-preview-plan`  
Codes: `DEPLOY_RESCUE_RESTORE_PREVIEW_PLAN_{READY|REVIEW_REQUIRED|BLOCKED}`

Bestehende Route `POST /api/deploy/rescue/restore-preview` (Deploy-Handoff-Runner) bleibt unverändert; Phase C.4 ergänzt die **Produkt-Orchestrierung** ohne Execute.

## Abgrenzung

- Keine ISO-Reife, keine Hardware-Reife
- Kein `tar -x`, kein rsync, kein Mount rw, kein Bootloader-Schreiben
- Operator-Override ersetzt **keine** Datensicherung des Ziels
