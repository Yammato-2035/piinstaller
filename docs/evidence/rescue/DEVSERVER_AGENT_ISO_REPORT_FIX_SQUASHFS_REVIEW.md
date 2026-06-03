# Devserver Agent ISO Report Fix — Squashfs Review

**ISO SHA256:** `614cc86ea865608f68524ef6d905a3baa1c0b1ce3dacaa9f1b80de6f541e0784` (alter Stand)

| Prüfung | Ergebnis |
|---------|----------|
| devserver_agent im Bundle/Squashfs | **yes** (`opt/setuphelfer-rescue/backend/devserver_agent/cli.py`) |
| Validator Import-Check (neu) | **FAIL exit 21** — alter Autopilot ohne `PYTHONPATH=.../backend` |
| Autopilot Unit im Squashfs | **yes** |
| Alter Autopilot-Aufruf | `-m backend.devserver_agent.cli`, PYTHONPATH nur `/opt/setuphelfer-rescue` |
| PYTHONPATH korrekt (alter ISO) | **no** |

## Status

`devserver_agent_present_wrong_module_call` + `validator_gap` (jetzt geschlossen durch erweiterten Validator)

Artefakt: `devserver_agent_iso_report_fix_current_iso_validator_latest.log` → **exit 21** `RESCUE-QEMU-AUTOPILOT-CALL-001`
