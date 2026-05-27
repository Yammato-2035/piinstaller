# Dev Dashboard Cockpit — Live Deploy Sync (5af715a)

**Datum:** 2026-05-27  
**HEAD (Workspace):** `5af715a`  
**Ziel:** Frontend/Cockpit-Stand `5af715a` nach `/opt/setuphelfer` — nur Deploy-Helper, keine Fachänderungen.

## Phase 0

| Prüfung | Ergebnis |
|---------|----------|
| Branch | `main` |
| HEAD | `5af715a` |
| `./scripts/check-runtime-deploy-gate.sh` | **Exit 0** (vor und nach Versuch) |

## Phase 1 — Deploy-Helper

| Schritt | Ergebnis |
|---------|----------|
| `sudo systemctl start setuphelfer-deploy-helper.service` | **Nicht ausgeführt** — `sudo` verlangt Passwort (Agent-Umgebung) |
| `systemctl status` danach | `inactive (dead)` |
| Letzter erfolgreicher Job | `deploy-20260527T193740Z-19726`, `head_before=3a4fc75`, `deploy_exit_code=0` |

**Folge:** `/opt` enthält den Frontend-Stand **vor** `5af715a` (letzter Deploy synchronisierte `3a4fc75`, nicht Cockpit-Roadmap-Fix).

### Operator (erforderlich)

```bash
sudo systemctl start setuphelfer-deploy-helper.service
./scripts/check-runtime-deploy-gate.sh
# Bundle-Check (optional):
grep -q greenVisibility.readyTitle /opt/setuphelfer/frontend/dist/assets/index-*.js && echo SYNC_OK
```

## Phase 2 — Live-API (lesend)

| Feld | Wert |
|------|------|
| `project_version` | `1.7.2` |
| `backend_runtime_path` | `/opt/setuphelfer/backend` |
| `deploy_drift.status` | **green** |
| `runtime_gate.passed` | **true** |
| `release_gate_status` | **rot** (unverändert, korrekt) |
| `roadmap.areas` | **13** |
| `GET /api/dev-dashboard/roadmap` | `status=success`, 13 areas |

## Cockpit-Sichtbarkeit (Bundle-Nachweis, nicht Browser)

| UI-Element | In `/opt` (live) | In Workspace-`dist` (5af715a) |
|------------|------------------|-------------------------------|
| `greenVisibility.readyTitle` (ReadyStable) | **nein** | **ja** |
| `dev-dashboard-ready-stable` | **nein** | **ja** |
| `roadmap.dataSource` (Banner) | **nein** | **ja** |
| `dev-dashboard-roadmap-panel` (älterer Stand) | **ja** | **ja** |

| Bewertung | |
|-----------|--|
| **RoadmapDrawer im Governance-Cockpit live** | **nein** (5af715a nicht in `/opt`) |
| **ReadyStableSection live** | **nein** |
| **Roadmap-Daten API** | **ja** (13 Bereiche) |
| **Rote/gelbe Gates** | **ja** (`release_gate=rot`, Rescue weiter gelb) |

## Phase 4 — Tests (Workspace, ohne Runtime-Aktion)

| Test | Ergebnis |
|------|----------|
| `npm --prefix frontend run build` | OK |
| `npm --prefix frontend run test -- --run` | 44 passed |
| `unittest backend.tests.test_dev_dashboard_v1` | OK |

## Fachliche Änderungen

**Keine** — nur Evidence; Deploy ausstehend (Operator-sudo).

## Nächster Prompt

`RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD` (nach erfolgreichem Helper-Deploy und Bundle-Check).
