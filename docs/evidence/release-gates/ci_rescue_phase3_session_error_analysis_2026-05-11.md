# CI Rescue Phase3 Session Error Analysis (2026-05-11)

## Ziel
Belegbar dokumentieren, wie der CI-Fehler in Phase3 Gate entstanden ist und wie er behoben wurde:

- Test: `tests/test_rescue_restore_phase3.py::TestRescueRestoreGate::test_session_missing`
- Erwartet: `rescue.restore.session_missing`
- Bekommen: `rescue.restore.dryrun_missing`

## Beobachtung (Fehlerbild)
Im GitHub Actions Lauf wurde der Gate-Fehlercode für eine fehlende Restore-Session nicht als `rescue.restore.session_missing` geliefert, sondern als `rescue.restore.dryrun_missing`.

Das bedeutet: In der Auswertung wurde so interpretiert, dass der erforderliche Dry-Run-Grant-Store (`load_dry_run_grant`) keinen Grant liefern konnte (bzw. dass der Test das nicht deterministisch gemockt hat).

## Lokale Reproduktion (pre-fix, commit f386ea1)
1. Testdatei auf den Stand **vor** dem Fix zurücksetzen:
   - `git checkout f386ea1 -- backend/tests/test_rescue_restore_phase3.py`
2. Dry-Run-Grant für Token `x` entfernen:
   - Zielpfad: `/tmp/setuphelfer-rescue-dryrun-state/x.json`
   - Falls vorhanden löschen (`rm -f .../x.json`)
3. Dann Test ausführen:
   - `cd backend`
   - `PI_INSTALLER_DEV=1 PYTHONPATH=. /tmp/piinstaller-test-venv/bin/python -m pytest tests/test_rescue_restore_phase3.py::TestRescueRestoreGate::test_session_missing -vv`

Ergebnis:
- pytest schlägt fehl mit Assertion-Fehler
- tatsächlicher Code: `rescue.restore.dryrun_missing`
- erwarteter Code: `rescue.restore.session_missing`

## Ursache (Kategorie D)
Kategorie D: **Mock-/Setup im Test erzeugt eigentlich `dryrun_missing` statt `session_missing`.**

Mechanik:
- `validate_restore_preconditions()` lädt zunächst den Dry-Run-Grant via `load_dry_run_grant(dry_run_token)`.
- Wenn der Grant nicht geliefert wird (`None`/falsy), wird direkt `rescue.restore.dryrun_missing` zurückgegeben – bevor überhaupt die Session-Logik (`session_missing`) greifen kann.
- Der Test `test_session_missing` hat den Dry-Run-Grant vor dem Fix nicht deterministisch gemockt, wodurch CI (ohne persistente `/tmp`-State) in den `dryrun_missing`-Pfad gefallen ist.

## Fix (commit b8af051)
In `backend/tests/test_rescue_restore_phase3.py` wurde in `test_session_missing` die Abhängigkeit deterministisch gemockt:

- Patch: `modules.rescue_restore_gate.load_dry_run_grant`
- Rückgabe: ein `grant_state` Dictionary mit
  - `session_id = "expected-session"`
  - `allow_restore = True`
  - `dryrun_mode = "dryrun"`
  - `dryrun_simulation_status = "DRYRUN_OK"`
  - u. a. `restore_decision`/`restore_risk_level`/`backup_file`/`target_device`
- Erwartung bleibt streng: `rescue.restore.session_missing`

Commit:
- `b8af051` — "Fix CI rescue phase3 session_missing code"

## Verifikation
Lokal (nach Fix):
- `cd backend && PYTHONPATH=. /tmp/piinstaller-test-venv/bin/python -m pytest tests/test_rescue_restore_phase3.py -q` => grün

CI:
- Neuer Run nach Fix: `25690310122`
- Der vorherige Session-Mismatch war nicht mehr der Stopper
- CI bricht nun bei einem anderen (Environment-/Permission-)Problem ab (SafeDevice-Mount unter `/media`).

## Sicherheits-/Produktlogik
- Es wurde keine Produktlogik (Rescue/Restore Engines) geändert.
- Der Fix betrifft ausschließlich den Test-Setup/Mocking und stellt sicher, dass `dryrun_missing` nicht fälschlich aus fehlendem `/tmp`-State resultiert.

