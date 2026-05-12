# Release Readiness – Bericht

**Generiert:** 2026-05-11 (nach Fix13-Analyse und Testpatch)  
**Gesamtstatus:** `blocked`

## Kurzfassung

Repo-Transparenz (Roadmap, Matrizen, Evidence-Templates) ist **angelegt**. **Deploy-Modul** auf `main` ergänzt (`df13af4`). **Fix13-CI-Fehler:** Ursache `_run_tar` bricht ohne nutzbares **systemd-inhibit** vor `run_command` ab (Kategorie D+E); **Test** minimal um inhibit-Mocks ergänzt — siehe `ci_fix13_backup_test_analysis_2026-05-11.md`. **GitHub CI:** `data/diagnostics` versioniert + `evidence_store`-Coerce auf **main**; Diagnostics-Mapping **nicht** mehr der -x-Blocker. smartctl Rescue-Dryrun Fix wurde durch `inspect_storage._run_capture` tolerant gemacht; **Phase3 Gate** `test_session_missing` ist behoben (Commit **b8af051**). Workspace-Sync **36d234b** inkl. Safe-Device-Test unter `/tmp/setuphelfer-test`; **Commit-Hygiene** siehe `post_workspace_sync_commit_hygiene_2026-05-11.md`. **Aktueller CI-Stand zu 36d234b:** Run **25691681846** — **failure**; erster -x-Fehler: `tests/test_deploy_runner_permission_boundary_v1.py::test_no_sudoers_file_written` (PermissionError bei `Path.exists` auf `/etc/sudoers.d/setuphelfer-runner`). **GitHub Actions sind nicht success** — kein „CI grün“. **BR-001** blocked, **Pytest** lokal weiter Snapshot siehe `current_failures.json`.

## Ampelüberblick

| Bereich | Status |
|---------|--------|
| Backup/Restore/Verify (Evidence) | Rot (BR-001 offen; Verify-Teil gelb) |
| Hardware | Rot |
| Rescue Stick real | Rot |
| CI-Nachweis aktuell | Rot — Fix13 Testpatch eingereicht; Remote-Lauf nach Push verifizieren (historisch: Run 25687412698) |
| Website live vs. Markdown | Rot |
| Affiliate | Gelb (Policies) |
| Legal | Rot |
| P0-Blocker | vorhanden (fehlende E2E-Evidence) |

## Empfehlung

**Nicht starten** bis mindestens ein dokumentierter Backup→Verify→Restore→Boot→Service-Zyklus auf freigegebenem Medium und aktuelle CI-Logs als Evidence vorliegen.

## Nächste Schritte

Siehe `STATUS_MATRIX.md` und Abschlussbericht der letzten Master-Prompt-Ausführung.
