# DCC Release Restore — After Fallback Live Acceptance (Operator Observation)

**Datum:** 2026-06-05  
**HEAD:** `a82b5f3`  
**Lauf-Typ:** Ingest / Acceptance (keine Reparatur, kein Deploy)

## Operator-Aktion

Operator hat **Release-Restore** nach local_lab-Smoke durchgeführt:

```bash
sudo install -m 0644 packaging/systemd/dropins/92-install-profile-release.conf.example \
  /etc/systemd/system/setuphelfer-backend.service.d/install-profile.conf
sudo systemctl daemon-reload && sudo systemctl restart setuphelfer-backend.service
```

## API-Wahrheit nach Release-Restore (read-only)

| Feld | Wert |
|------|------|
| `install_profile` | `release` |
| `profile_gate_status` | `green` |
| `dev_control_enabled` | `false` |
| `backend_runtime_path` | `/opt/setuphelfer/backend` |
| `/api/dev-dashboard/status` | HTTP **404** `PROFILE_ROUTE_BLOCKED` |
| `/api/fleet/sessions` | HTTP **404** `PROFILE_ROUTE_BLOCKED` |
| `/api/dev-dashboard/recent-evidence` | HTTP **404** `PROFILE_ROUTE_BLOCKED` |
| UI `:3001/?window=cockpit` | HTTP **200** |

Portlage: API `:8000`, DCC `:3001`, nginx `:8080` nicht DCC — **kein Portfehler**, **kein Backend-down**.

## Served Bundle (unverändert korrekt)

| Prüfung | Ergebnis |
|---------|----------|
| Asset | `assets/index-FgGYQFBB.js` |
| Marker | `DCC_BOOT_DIAGNOSTICS_V1`, `dcc-boot-diagnostics`, `dcc-cockpit-shell`, `dev-control-disabled`, `PROFILE_ROUTE_BLOCKED` |

## Operator-Browserbefund (Release)

| Befund | Status |
|--------|--------|
| UI unter `:3001` erreichbar | **ja** |
| Browser bleibt **nicht** leer | **ja** |
| Disabled-Page sichtbar (`dev-control-disabled`) | **ja** |
| Boot-/Fallback-Diagnosepanel sichtbar | **ja** |

Konsistent mit Fail-safe-UI: bei `PROFILE_ROUTE_BLOCKED` zeigt das Frontend `profile_blocked_release` + persistentes Diagnosepanel.

## Vorheriger local_lab-Smoke (bereits in Evidence)

Siehe `DCC_LIVE_ACCEPTANCE_AFTER_FALLBACK_OPERATOR_OBSERVATION.md`:

* `local_lab`, `dev_control_enabled=true`
* `/api/dev-dashboard/status` HTTP **200**
* Operator: DCC + Boot-Diagnose sichtbar

## Klassifikation

```text
status=green
classification=dcc_live_acceptance_complete
blank_dcc_screen=resolved
release_restore=confirmed
local_lab_smoke=confirmed
```

`404 PROFILE_ROUTE_BLOCKED` unter `release` ist **korrekt** — erwarteter Sicherheitszustand, kein Fehler.

## DCC-Track-Status

**DCC Blank-Screen-Track beendet.** Keine weitere Blank-Screen-Reparatur.

**Nächster Schritt:** `RUNTIME_GOVERNANCE_LIVE_VALIDATION` → danach `MONOLITH_BOUNDARY_FOLLOWUP`.

Controlled Command Runner (`DEV_DASHBOARD_CONTROLLED_COMMAND_RUNS_MVP`) bleibt zurückgestellt.
