# Developer DCC Status Route — Capability Gate Fix

**Status:** `workspace_fix_verified_awaiting_operator_deploy`  
**Datum:** 2026-06-07

## Problem

Unter `install_profile=release` mit gültiger lokaler Developer-Capability:

| Endpunkt | Verhalten (vor Fix) |
|----------|---------------------|
| `/api/dev-dashboard/capability-status` | 200, `dcc_visible=true`, `reason=DEVELOPER_CAPABILITY_VALID` |
| `/api/dev-dashboard/status` | Fehler-Body `PROFILE_ROUTE_BLOCKED`, `required_profile=local_lab` |

Middleware ließ Requests mit gültigem Token durch; der **Handler** blockierte danach erneut über `dev_control_enabled` allein.

## Fix

`backend/core/dev_dashboard_status_service.py`:

- `build_dcc_profile_block_response()` nutzt jetzt `is_dcc_route_allowed()` (zentrales Capability-Gate)
- `required_profile: local_lab` entfernt
- `build_dev_dashboard_status()` und `/api/dev-dashboard/backend-health` übergeben Request-Header

## Erwartetes Verhalten (nach Deploy)

| Szenario | `/api/dev-dashboard/status` |
|----------|----------------------------|
| Release, kein Token | HTTP **404** `PROFILE_ROUTE_BLOCKED` (Middleware) |
| Release, gültiger `X-Setuphelfer-Developer-Token` | HTTP **200**, echter DCC-Status |
| Telemetrie `/api/rescue/telemetry/health` | HTTP **200**, unabhängig vom DCC-Token |

## Weitere DCC-Routen (Audit-Vorbereitung)

**Interne Profilprüfung (jetzt Capability-Gate):**

- `/api/dev-dashboard/status`
- `/api/dev-dashboard/backend-health`

**Nur Middleware-Gate** (keine doppelte `dev_control`-Prüfung im Handler):

- modules, evidence-index, control-center-summary, roadmap, rescue-build, rescue-iso, notifications, deploy, update, packaging, project-overview, actions, …

**Diagnose immer erreichbar:**

- `/api/dev-dashboard/capability-status`

Vollständige Prüfung aller Handler: Next Prompt **`DEVELOPER_DCC_FULL_ROUTE_CAPABILITY_AUDIT`**.

## Tests

```bash
PYTHONPATH=backend backend/venv/bin/python3 -m pytest \
  backend/tests/test_dev_dashboard_status_service_v1.py \
  backend/tests/test_developer_capability_v1.py \
  backend/tests/test_runtime_governance_route_exposure_v1.py -q
```

Ergebnis Workspace: **31 passed**. Kein Token-Wert in Testausgaben.

## Operator-Follow-up

1. `sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller` (mit Freigabe)
2. Smoke mit lokalem Token wiederholen
3. Erst danach USB-Write (`RESCUE_USB_WRITE_OPERATOR_FOR_WINDOWS_INSPECT`)

## Secrets

Kein Token-Wert in diesem Dokument oder in JSON.
