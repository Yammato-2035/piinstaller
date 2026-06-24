# CI Green Loop Audit — 2026-06-24

## Phase 0 — Ausgangslage

| Feld | Wert |
|------|------|
| **HEAD** | `d535b94` — `fix(tests): restore green pytest suite without weakening gates` |
| **Branch** | `main` |
| **Staged (Preflight)** | *keine* — `git diff --cached --name-only` leer |
| **Letzter CI-Run** | `28073834208` — **failure** (Pytest) |
| **Letzter Security-Run** | `28073834221` — **success** |

Preflight-Bundle (`scripts/preflight-before-push.sh`, `.github/workflows/ci.yml` preflight-Job) liegt **unstaged/untracked** und wurde nicht vermischt.

## Fehlergruppen

| Gruppe | Tests | Fehlerbild | Ursache | Entscheidung | Fix-Plan |
|--------|-------|------------|---------|--------------|----------|
| fixture_or_seed_missing | `test_dev_dashboard_rescue_build_status_v1::test_usb_write_stays_false` | `AssertionError: True is not false` auf `usb_write_allowed` | Test ruft `build_rescue_build_dashboard_state()` ohne Isolation auf; getrackte Evidence `docs/evidence/runtime-results/rescue/usb_operator_selection_latest.json` enthält `write_allowed: true` | Test-Contract anpassen (Isolation), Safety-Ziel beibehalten | `patch(load_operator_selection_evidence, return_value=None)` — gleiches Muster wie fehlende Evidence in Temp-Repos |
| runtime_required_in_ci | `test_dev_dashboard_v1::test_runtime_gate_allows_yellow_drift_without_actionable_suggestions` | `AssertionError: False is not true` auf `passed` | `build_runtime_gate` prüft `systemctl is-active setuphelfer-backend.service`; lokal aktiv, CI-Runner ohne Dienst | Unit-Test isolieren: Mock `_systemd_unit_state` → `active` | `@patch` auf Cockpit-Test |

## Fix-Nachweise

| Fehler | Ursache | Fix | Nachweis |
|--------|---------|-----|----------|
| `test_usb_write_stays_false` CI-ROT | Getrackte Operator-Selection-Evidence mit `write_allowed: true` | Mock `load_operator_selection_evidence` → `None` | Lokal: `pytest tests/test_dev_dashboard_rescue_build_status_v1.py` grün; Commit `c2f06c6` |
| `test_runtime_gate_allows_yellow_drift_without_actionable_suggestions` CI-ROT | Systemd-Abhängigkeit im Unit-Test | Mock `_systemd_unit_state` → `active` | Lokal: Test grün auch bei simuliertem `inactive` Service |

## Ergebnis

- **local_pytest_status:** grün (venv, `--maxfail=0`, 3529 passed, 2 skipped)
- **local_pytest_count:** 3529 passed / 2 skipped (inkl. untracked Tests im Workspace)
- **remote_ci_status:** *nach Fix-Commit ausstehend*
- **remote_ci_run:** `28073834208` (vor Fix)
- **security_status:** grün (`28073834221`)
- **commits:** *siehe Push*
- **remaining_failures:** keine CI-relevanten auf committed `main` nach Fix erwartet

## Behobene Gruppen

| Gruppe | Fix | Commit |
|--------|-----|--------|
| fixture_or_seed_missing | Operator-Evidence im Test isolieren | *pending* |

## Bewusst nicht geändert

- Preflight-Bundle (unstaged/untracked)
- Historische Evidence (`usb_operator_selection_latest.json` bleibt — korrektes Runtime-Artefakt)
- Rescue-Artefakte, Telemetrie, MSI/Stick
- Hardware-/Runtime-Tests

## Nächster Schritt

1. CI nach Push verifizieren
2. Preflight-Bundle separat prüfen und committen
3. Rettungsstick/MSI fortsetzen
