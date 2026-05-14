# Evidence-Verzeichnis (Setuphelfer)

Dieses Verzeichnis sammelt **maschinenlesbare und nachvollziehbare** Testnachweise. Eine Ampel **Grün** ist nur gerechtfertigt, wenn hier (oder verlinkt) vollständige Evidence liegt: Zeitstempel, Umgebung, Version, reproduzierbare Schritte, Logs/Auszüge.

## Ordner

| Ordner | Inhalt |
|--------|--------|
| `hardware/` | Hardwareläufe (Pi, Laptop, Medien) |
| `backup-restore/` | Backup, Verify, Restore, Fehlerfälle, **externe Zielrichtlinie** (`BR-001_external_target_*`, `BACKUP_TARGET_POLICY_*`) |
| `rescue-stick/` | Read-only Rescue-/Live-Flows |
| `website/` | Transparenz-, Status-, Affiliate-Checks |
| `release-gates/` | Sammelgates … **`backend_version_update_gate.json`**, **`apt_update_delivery_gap.json`**, … |

## Schema

JSON-Dateien nutzen das Feld `schema: "setuphelfer.evidence.v1"`. Pflichtfelder für **abgenommene** Evidence:

- `executed_at` (ISO-8601)
- `environment` (OS, Arch, Gerät, Medien)
- `result` (ok / fail / blocked)
- `artifacts` (Pfade zu Logs, Screenshots, Exporten)
- `evidence_complete: true`

Templates mit `evidence_complete: false` sind **kein** Grün-Nachweis.

## Regel

> Grün gibt es nur mit Testnachweis, Doku und Evidence-Datei.

Keine Grün-Markierung allein aufgrund von Code-Review oder `py_compile`.

**STRICT Backup/Verify-Kette:** BR-004 und BR-005 gelten nur dann als abgenommen, wenn sie **dasselbe Archiv** prüfen, das BR-001 auf einem **freigegebenen** externen Ziel erzeugt hat (siehe `docs/testing/BACKUP_RESTORE_TEST_MATRIX.md`, `docs/evidence/release-gates/backup_restore_release_gate.json`). **Hinweis 2026-05-12:** Betreiber-Mount-Beispiel **`/media/gabriel/setuphelfer-back`**. Shell vs. API: **`BR-001_productive_target_check_media_path_analysis_2026-05-12.md`**. **Workspace-Diagnosefix (Traverse):** **`BR-001_target_permission_diagnostics_fix_2026-05-12.md`** (**STORAGE-006**, **`backup.target_traverse_denied`**). Policy: **`BR-001_path_policy_correction_2026-05-12.md`**, **`BR-001.json`**. **Hinweis 2026-05-14 (BR-013 Ziel-Schreib-EIO):** Job **`f744c2936468`**, Evidence **`BR-001_write_io_error_2026-05-14.md`**, KB **`docs/knowledge-base/backup/BACKUP_TARGET_WRITE_IO_ERROR.md`**, API-Code **`backup.write_io_error`** / **`BACKUP-IO-ERROR-050`**. **Hinweis 2026-05-14 (BR-012 Runner-Finalisierung):** Job **`2cff11287f67`**, Fix **`backup_runner.py`**, Evidence **`BR-001_runner_finalization_performance_failure_2026-05-14.md`** (Abschnitt 6 Deploy-Prep: Version-Gate, SHA256 Workspace=`/opt`, systemd-Timeouts, kein POST create). JSON **`br001_runner_fix_deploy_prep_2026_05_14`**. **Hinweis 2026-05-13 (BR-011 Preflight-Design):** Spezifikation *Backup Package Activity Preflight* — **`docs/backup/BACKUP_PACKAGE_ACTIVITY_PREFLIGHT_DE.md`**, **`docs/knowledge-base/backup/BACKUP_PACKAGE_ACTIVITY_PREFLIGHT.md`**, Matrix **BR-011**. **Hinweis 2026-05-13 (Timer-pause Retry STOP):** Phase 2 (`mintUpdate`, unattended) + fehlendes **`sudo`** — **`BR-001_package_timer_paused_retry_2026-05-13.md`**. **Hinweis 2026-05-13 (BR-001 Paketaktivität):** Job **`e341a326ac69`** — **`backup.blocked_package_activity`** / **`UPDATE-CONFLICT-041`** ( **`apt-get autoremove --purge -y`**, Mint-Timer) — Evidence **`BR-001_package_activity_failure_2026-05-13.md`**, Runbook **`BR-001_package_activity_retry_runbook_2026-05-13.md`**. **Hinweis 2026-05-13 (stale-sync Deploy-Retry):** Operator-**`sudo`** auf dem Host für **`install`** **`app.py`** + **`systemctl restart`** — Agent-Run **blockiert** (TTY) — **`BR-001_stale_job_sync_fix_and_retry_2026-05-13.md`**. **Hinweis 2026-05-13 (Runner systemd):** **`setuphelfer-backup@.service`** — **`ReadWritePaths`** muss **`/media/gabriel/setuphelfer-back`** enthalten; stale **`status.json`**/**`backup.job_conflict`** — **`BR-001_runner_systemd_readwritepaths_fix_2026-05-13.md`**. **Hinweis 2026-05-13 (Starter-Retry):** **`sudo install`** des Repo-Starters nach **`/usr/lib/setuphelfer/`** im Agent **blockiert** — **`BR-001_starter_update_and_retry_2026-05-13.md`**. **Hinweis 2026-05-13 (Full-Backup-Versuch):** `POST /api/backup/create` auf **`/media/gabriel/setuphelfer-back`** → **`backup.starter_invalid_path`** bis Starter deployed — **`BR-001_full_backup_run_2026-05-13.md`**. **Hinweis 2026-05-13 (systemd):** Shell-**`rw`** vs. API-**EROFS** auf **`/media/gabriel/setuphelfer-back`** — **`ReadWritePaths`** in Service-Unit ergänzt (**`BR-001_systemd_readwritepaths_analysis_2026-05-13.md`**, Drop-in-Beispiel **`docs/operations/systemd/setuphelfer-backend-backup-target.conf.example`**). **Hinweis 2026-05-13 (produktiv):** `/api/version` → HTTP 500 durch Legacy **`/opt/setuphelfer/config/version.json`** (Backend-`.py` bereits Workspace-SHA256); **`target-check`** nur **`/media/gabriel/setuphelfer-back`** — `backup.backup_target_not_writable`, Shell **`findmnt` rw** vs. API **`ro`** — **`BR-001_backend_update_and_version_fix_2026-05-13.md`**, **`BR-001_readonly_target_and_api500_analysis_2026-05-12.md`**. Strategischer Doku-Pfad **`/media/setuphelfer/setuphelfer-back`** (nur auf externem Medium); externe Priorität: **`docs/backup/BACKUP_TARGET_POLICY_DE.md`** / **`EN.md`**; **Deploy** nach `/opt`: Runbook + sha256 in **`BR-001_backend_deploy_status_2026-05-12.md`** (vom Operator auf dem Host auszuführen, falls Agent kein `sudo` hat).
