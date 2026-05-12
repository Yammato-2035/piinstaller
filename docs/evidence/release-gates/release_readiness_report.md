# Release Readiness – Bericht

**Generiert:** 2026-05-11 (nach Fix13-Analyse und Testpatch)  
**Gesamtstatus:** `blocked`

## Kurzfassung

Repo-Transparenz (Roadmap, Matrizen, Evidence-Templates) ist **angelegt**. **Deploy-Modul** auf `main` ergänzt (`df13af4`). **Fix13-CI-Fehler:** Ursache `_run_tar` bricht ohne nutzbares **systemd-inhibit** vor `run_command` ab (Kategorie D+E); **Test** minimal um inhibit-Mocks ergänzt — siehe `ci_fix13_backup_test_analysis_2026-05-11.md`. **GitHub CI:** `data/diagnostics` versioniert + `evidence_store`-Coerce auf **main**; Diagnostics-Mapping **nicht** mehr der -x-Blocker. smartctl Rescue-Dryrun Fix wurde durch `inspect_storage._run_capture` tolerant gemacht; **Phase3 Gate** `test_session_missing` ist behoben (Commit **b8af051**). Workspace-Sync **36d234b**; Hygiene-Commit **7e0323b** — Inventare + `post_workspace_sync_commit_hygiene_2026-05-11.md`. **Deploy-Runner sudoers-Boundary:** `ci_deploy_runner_permission_boundary_analysis_2026-05-11.md`. **Deploy-Write-Harness:** `ci_deploy_write_harness_mnt_setuphelfer_analysis_2026-05-11.md` — Test-Cache unter `backend/cache/deploy` statt `/mnt/setuphelfer`. **Letzter dokumentierter CI-Lauf:** Run **25750787235** — **failure** (historisch Harness /mnt); **Referenz** 36d234b: Run **25691681846**. **GitHub Actions success** nach Harness-Push nachzuweisen — kein „CI grün“. **BR-001** blocked, **Pytest** lokal siehe `current_failures.json`.

## Ampelüberblick

| Bereich | Status |
|---------|--------|
| Backup/Restore/Verify (Evidence) | Rot (BR-001 offen; Verify-Teil gelb) |
| Hardware | Rot |
| Rescue Stick real | Rot |
| CI-Nachweis aktuell | Rot — Run **25750787235** (historisch Harness /mnt); Harness-Portabilität + sudoers-Boundary dokumentiert — **success** erst nach neuem Push |
| Website live vs. Markdown | Rot |
| Affiliate | Gelb (Policies) |
| Legal | Rot |
| P0-Blocker | vorhanden (fehlende E2E-Evidence) |

## Empfehlung

**Nicht starten** bis mindestens ein dokumentierter Backup→Verify→Restore→Boot→Service-Zyklus auf freigegebenem Medium und aktuelle CI-Logs als Evidence vorliegen.

## Nächste Schritte

Siehe `STATUS_MATRIX.md` und Abschlussbericht der letzten Master-Prompt-Ausführung.
