# R.3 — TUI-Menü-Stabilität

**Ziel:** Menü darf nicht abstürzen; Fehler sammeln und kontrolliert zurückkehren.

## Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| `setuphelfer-rescue-start-assistant` | `_main_menu`: try/except pro Aktion, Evidence-Record, Bundle am Ende |
| `setuphelfer-rescue-common.sh` | `setuphelfer_rescue_record_menu_evidence`, `setuphelfer_rescue_run_evidence_bundle` |
| `setuphelfer-rescue-evidence.py` | Subcommand `menu-action` |

## Regeln (unverändert)

- `"write_actions_allowed": false` im Assistenten-State
- Kein Restore/Backup-Execute aus dem Menü
- Jede Menüaktion → `setuphelfer-evidence/menu/`

## Tests

`backend/tests/test_rescue_tui_menu_stability_r3.py` — statische Shell-Checks (4 Tests, OK):

- Evidence-Recording in `_main_menu`
- Bundle auf Exit
- Common-Helper vorhanden
- Write-Actions weiterhin blockiert

## Menüaktionen abgedeckt

WLAN, Telemetrie, Logs sichern, Diagnose, Hardware, Exit/Reboot/Shell — jeweils mit `plan_builder_exit_*` Fehlerpfad.
