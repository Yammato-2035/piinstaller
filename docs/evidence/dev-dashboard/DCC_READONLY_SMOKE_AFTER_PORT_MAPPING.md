# DCC Read-Only Smoke nach Port-Mapping

**Stand:** 2026-06-02  
**Status:** **ok** (`local_lab` aktiv)

## Port-Checks

| Ziel | HTTP | Server / Anmerkung |
|------|------|---------------------|
| `http://127.0.0.1:3001/` | 200 | `SimpleHTTP/0.6 Python/3.12.3` — UI ok |
| `http://127.0.0.1:3001/?window=cockpit` | 200 | gleiche SPA (Cockpit-Parameter) |
| `http://127.0.0.1:8080/` | 200 | `nginx/1.24.0` — **nicht SetupHelfer** |
| `http://127.0.0.1:8000/api/version` | 200 | `install_profile=local_lab`, `dev_control_enabled=true` |
| `http://127.0.0.1:8000/api/dev-dashboard/status` | 200 | ~166 577 B JSON |
| `http://127.0.0.1:8000/api/fleet/sessions` | 200 | Fleet API ok |

## Bewertung

| Kriterium | Ergebnis |
|-----------|----------|
| UI-Port 3001 | ok |
| API-Port 8000 | ok |
| Port 8080 | ignoriert (nginx) |
| DCC-API unter `release` | würde `blocked_by_profile_expected` sein — aktuell **local_lab** |

## 8080 ausgeschlossen

**yes** — kein SetupHelfer-DCC-Fehler auf Port 8080.

## Nach Fleet-Smoke (Release-Pfad)

| Kontext | DCC-API |
|---------|---------|
| `local_lab` (aktuell) | 200 — **ok** |
| `release` (Ziel nach Restore) | 404 `PROFILE_ROUTE_BLOCKED` — **blocked_by_profile_expected**, kein Fehler |

Port-Mapping bleibt **green** (3001 UI, 8000 API, 8080 nginx).
