# Rescue Agent Contract Result (Strict Static Pass)

**Commit-Prep:** 2026-06-02 — pytest 32 (rescue_agent+fleet heartbeat), Frontend 54 Vitest; kein Deploy.

## Phase-0 Gate

- Runtime-Gate: `check-runtime-deploy-gate: LEGACY_GATE_NON_PROFILE_AWARE`
- Entscheidung: `runtime_gate_blocked_static_analysis_only`
- Keine Runtime-Smokes auf Port 8000 in diesem Lauf

## Ergebnis

- Fleet Heartbeat Contract: `implemented` (`agent_state`, running-neutralisierung)
- Rescue Discovery: `implemented_stub`
- Pairing: `implemented_stub`
- E2EE: `contract_stub`
- nftables: `preview_only` (`apply_allowed=false`)
- System Report: `implemented_stub`
- API Contract: `implemented_stub`
- Router-Startability-Härtung: `implemented`
  - `rescue_agent_router_status` + `rescue_agent_router_error` in `/api/version`
  - kein Backend-Startabbruch bei optionalem Router-Importfehler

## Sicherheits- und Scope-Guards

- Kein ISO-Build: yes
- Kein QEMU: yes
- Kein USB/dd: yes
- Kein Backup: yes
- Kein Restore: yes
- Kein apt install/upgrade: yes
- Kein Push: yes

## Startability-Befund (DCC)

- Laufende Runtime:
  - `/api/version` antwortet `200`
  - `/api/dev-dashboard/status` in `release` korrekt `404 PROFILE_ROUTE_BLOCKED`
- Runtime-Python nachgewiesen:
  - `/opt/setuphelfer/backend/venv/bin/python3`
  - fastapi/pydantic vorhanden
- Backend-Import mit Runtime-Python gegen Workspace-Code:
  - `APP_IMPORT_OK`
  - Rescue-Agent-Module importierbar
- Deploy-Drift bleibt:
  - `/opt/setuphelfer/backend/rescue_agent` fehlt
  - `backend/app.py` und weitere Kerndateien differieren
  - neue `/api/version`-Routerdiagnosefelder daher live noch nicht sichtbar
