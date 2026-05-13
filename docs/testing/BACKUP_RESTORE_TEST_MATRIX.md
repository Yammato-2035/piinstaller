# Setuphelfer Backup-/Restore-Testmatrix

| ID | Test | Voraussetzung | Erwartung | Status | Evidence |
|----|------|---------------|-----------|--------|----------|
| BR-001 | Full Backup freigegebenes Ziel | Nur **`/media/gabriel/setuphelfer-back`**; Phase 2 ohne Paketprozesse; Timer nur temp. stop/start (nicht disable); sudo für Locks/Timer | Archiv + Manifest + SHA256 | Rot (blocked — Retry STOP Phase 2 oder sudo; Evidence **`BR-001_package_timer_paused_retry_2026-05-13.md`**) | `BR-001_package_activity_failure_2026-05-13.md`, `BR-001_package_activity_retry_runbook_2026-05-13.md`, `BR-001.json` |
| BR-002 | Ziel nicht beschreibbar | Rechte entzogen | harter Abbruch | Rot | docs/evidence/backup-restore/BR-002.json |
| BR-003 | `.partial` Archiv prüfen | abgebrochene Sicherung | Verify blockiert | Rot | docs/evidence/backup-restore/BR-003.json |
| BR-004 | Verify Basic gültig | **dieselbe** Archivdatei wie BR-001 | ok | Rot (blocked — BR-001) | docs/evidence/backup-restore/BR-004.json |
| BR-005 | Verify Deep gültig | **dieselbe** Archivdatei wie BR-001 | ok | Rot (blocked — BR-001) | docs/evidence/backup-restore/BR-005.json |
| BR-006 | Verify beschädigt | manipuliertes Archiv | hash_mismatch / corrupt | Rot | docs/evidence/backup-restore/BR-006.json |
| BR-007 | Restore Preview | gültiges Archiv | keine Schreiboperation | Rot | docs/evidence/backup-restore/BR-007.json |
| BR-008 | Restore externes Ziel | freigegebenes Medium | Restore erfolgreich | Rot | docs/evidence/backup-restore/BR-008.json |
| BR-009 | Interne Disk Schutz | interne Systemplatte | blockiert | Rot | docs/evidence/backup-restore/BR-009.json |
| BR-010 | Boot nach Restore | restored System | bootfähig | Rot | docs/evidence/backup-restore/BR-010.json |

## Verknüpfung Unit-/CI-Tests

Viele Szenarien haben Abdeckung unter `backend/tests/` (z. B. Backup/Restore/Write-Guard). **Grün in dieser Matrix** verlangt zusätzlich dokumentierte Läufe mit Evidence-JSON gemäß `docs/evidence/README.md`.

**STRICT-Kette (2026-05-13):** Timer-pause-Retry-Versuch — **STOP Phase 2** (`mintUpdate`, `unattended-upgrade-shutdown`) + **sudo** fehlt für `fuser`/Timer — **`BR-001_package_timer_paused_retry_2026-05-13.md`**. Zuvor Job **`e341a326ac69`** **`backup.blocked_package_activity`** — **`BR-001_package_activity_failure_2026-05-13.md`**. Früher: EROFS/stale-sync … **`BR-001_runner_systemd_readwritepaths_fix_2026-05-13.md`**, **`BR-001_stale_job_sync_fix_and_retry_2026-05-13.md`**, Starter **`BR-001_full_backup_run_2026-05-13.md`**.
