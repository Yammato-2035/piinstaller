# Developer Dashboard — IST-Stand (Latest)

**Erzeugt:** 2026-05-27  
**Branch:** `main`  
**HEAD:** `20a8303` (vor Roadmap-Sichtbarkeits-Fix-Commit)

## Phase-0-Gate

| Prüfung | Ergebnis |
|---------|----------|
| `./scripts/check-runtime-deploy-gate.sh` | **Exit 0** — OK (Version, Pfad, deploy_drift/Manifest) |
| `runtime_gate_blocked_static_analysis_only` | **false** |

## Live-API (Port 8000, belegt)

| Feld | Wert |
|------|------|
| `project_version` | `1.7.2` |
| `backend_runtime_path` | `/opt/setuphelfer/backend` |
| `deploy_drift.status` | `green` |
| `runtime_gate.passed` | `true` |
| `runtime_gate.status` | `green` |
| `safe_test_mode.locked` | `false` |
| `release_gate_status` | `rot` |
| `dashboard.roadmap.areas` | **13** Einträge |
| `rescue-iso/status` | `yellow`, `usb_write.allowed=false` |

## Workspace (getrennt)

- Viele uncommittete Änderungen (u. a. `VERSION`, `ckb-next`, Rescue-Evidence, Cursor-Rules).
- `packaging/helpers/setuphelfer-backup-starter.py` weiterhin lokal dirty (Host-Allowlist).
- Frontend-Fix für Roadmap-Sichtbarkeit im Workspace, **nicht** in `/opt` bis separater Deploy.

## Dienste (ohne sudo)

- `setuphelfer-backend.service`: **active**
- `setuphelfer-deploy-helper.service`: **inactive**
