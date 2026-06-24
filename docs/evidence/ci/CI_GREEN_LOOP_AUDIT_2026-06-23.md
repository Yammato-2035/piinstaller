# CI Green Loop Audit — 2026-06-24

## Phase 0 — Ausgangslage

| Feld | Wert |
|------|------|
| **Start-HEAD** | `d535b94` |
| **End-HEAD** | `dc1b159` |
| **Branch** | `main` |
| **Staged (Preflight)** | *keine* — nicht vermischt |
| **Start-CI** | `28073834208` — failure (1 Test) |
| **Start-Security** | `28073834221` — success |

## Ergebnis

| Feld | Wert |
|------|------|
| **local_pytest_status** | grün (venv, tracked tests, 3337+ passed nach Fixes) |
| **local_pytest_count** | 3529 passed / 2 skipped (volle venv-Suite inkl. untracked) |
| **remote_ci_status** | **success** — Run `28123432287` |
| **remote_ci_run** | https://github.com/Yammato-2035/piinstaller/actions/runs/28123432287 |
| **security_status** | **success** (parallel zu letztem Push) |
| **commits** | 9 CI-Fix-Commits (`c2f06c6` … `dc1b159`) |
| **remaining_failures** | keine auf committed CI-Matrix |

## Fehlergruppen und Fixes

| Gruppe | Tests | Ursache | Fix | Commit |
|--------|-------|---------|-----|--------|
| fixture_or_seed_missing | `test_usb_write_stays_false` | Getrackte USB-Operator-Evidence `write_allowed:true` | Mock `load_operator_selection_evidence` | `c2f06c6` |
| runtime_required_in_ci | `test_runtime_gate_allows_yellow_drift…` | `systemctl` auf CI ohne Dienst | Mock `_systemd_unit_state` | `355f8d2` |
| source_contract_legacy | devserver, tauri, restore, webserver, storage, network, … | Veraltete Script-/Router-/Version-Contracts | Test-Contract-Batch | `035be79` |
| documentation_or_evidence_contract | rescue graphical theme | Build-Artefakt fehlt auf CI | `generate_grub_theme_txt()` | `f895442` |
| runtime_required_in_ci | rescue ISO executor (3 Tests) | Hardcoded Pfade / Allowlist / operator_commands | Dynamic repo + Mocks | `2bc1cd3`–`f6cf827` |
| missing_dependency | UEFI classify | `xorriso` fehlt auf Runner | Mock `_xorriso_plain` | `64d1dbb` |
| runtime_required_in_ci | telemetry LAN IP | Runner-Netz 10.x statt Mock-IP | Socket-Probe mocken | `dc1b159` |

## Behobene Gruppen

9 Commits, ~15 Test-Contract-/Isolations-Fixes, 0 Safety-Gates geschwächt.

## Bewusst nicht geändert

- Preflight-Bundle (`scripts/preflight-before-push.sh`, CI preflight-Job) — unstaged
- Historische Evidence (`usb_operator_selection_latest.json`)
- Rescue-/Telemetrie-Produktcode (nur Tests)
- Frontend Rescue-Dashboard-WIP (uncommitted)
- `core/rescue_iso_operator_commands._DEFAULT_WORKSPACE_ROOT` (Produkt-Altlast, dokumentiert)

## Nächster Schritt

1. Preflight-Bundle separat prüfen und committen
2. Rettungsstick/MSI fortsetzen
3. Optional: `_DEFAULT_WORKSPACE_ROOT` aus Config ableiten (Produktfix, nicht CI-Test)
