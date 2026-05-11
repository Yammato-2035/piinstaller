# Release Readiness – Bericht

**Generiert:** 2026-05-11 (nach Fix13-Analyse und Testpatch)  
**Gesamtstatus:** `blocked`

## Kurzfassung

Repo-Transparenz (Roadmap, Matrizen, Evidence-Templates) ist **angelegt**. **Deploy-Modul** auf `main` ergänzt (`df13af4`). **Fix13-CI-Fehler:** Ursache `_run_tar` bricht ohne nutzbares **systemd-inhibit** vor `run_command` ab (Kategorie D+E); **Test** minimal um inhibit-Mocks ergänzt — siehe `ci_fix13_backup_test_analysis_2026-05-11.md`. **GitHub CI:** `data/diagnostics` versioniert + `evidence_store`-Coerce auf **main**; Diagnostics-Mapping **nicht** mehr der -x-Blocker. smartctl Rescue-Dryrun Fix wurde durch `inspect_storage._run_capture` tolerant gemacht; aktueller Rescue/Restore-Blocker: **Phase3 Gate** `test_session_missing` (Code-Mismatch `dryrun_missing` vs. `session_missing`, Run **25689506120**). **BR-001** blocked, **Pytest** lokal **1526/0**.

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
