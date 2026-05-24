# Rescue Build Dashboard — IST-Analyse

**Datum:** 2026-05-24
**Git HEAD:** `f70a6ea`

## Vorhandene Dashboard-Endpunkte

| Endpoint | Zweck |
|----------|--------|
| `GET /api/dev-dashboard/status` | Gesamtstatus Cockpit |
| `GET /api/dev-dashboard/modules` | Modul-Liste |
| `GET /api/dev-dashboard/evidence-index` | Evidence-Index |
| `GET /api/dev-dashboard/prompt-findings` | KI-Export |
| `GET /api/deploy/rescue-stick/build-emulation/*` | Read-only Emulation (10 Routen) |

**Fehlend (vor Integration):** zentraler Rescue-Build-Status mit Gates, Logs, ISO-Artefakten.

## Vorhandene Governance-Felder

- `RescueStickBoard` — BR-001-LIVE/OFFLINE Release-Gates
- Governance-Matrix Bereich `rescue`
- `runtime_gate`, `deploy_drift`, `safe_test_mode` in Cockpit

## Evidence-Quellen (Rescue)

- `docs/evidence/rescue/RESCUE_CONTROLLED_ISO_BUILD_RESULT.md`
- `docs/evidence/rescue/RESCUE_CONTROLLED_LIVE_BUILD_TOOL_CHECK.md`
- `docs/evidence/runtime-results/handoff/rescue_stick_readonly_build_final_gate.json`
- Build-Logs bisher nur `/tmp/setuphelfer-lb-build*.log` (manuell)

## Fehlende Rescue-Build-Gates (vor Integration)

- Toolcheck-Aggregation im Dashboard
- Temp-Runtime-Bundle-Gate live
- Live-Build-Tree-Gate live
- ISO-Build-Gate + letzter Fehler
- USB-Write-Gate explizit
- Live-OS-Validation-Gate
- Log-Tail + SHA256-Anzeige
- Nächste Operator-Aktion

## Empfehlung minimal-invasiv

1. `backend/core/rescue_build_dashboard_state.py` — read-only Aggregation
2. `GET /api/dev-dashboard/rescue-build/status`
3. `RescueBuildPanel` im External Development Control Center
4. `run-controlled-iso-build-with-logging.sh` — persistente Logs + summary.json
5. Keine Build/USB-Buttons in Phase 1
