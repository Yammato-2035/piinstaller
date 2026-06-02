# Development Control Center — Ports und URLs

**Stand:** 2026-06-02

## Produktiv-Runtime (typisch nach `deploy-to-opt`)

| Port | Service | Rolle |
|-----:|---------|--------|
| **3001** | `setuphelfer.service` | Statisches Frontend (`frontend/dist`) via `serve-frontend-production.py` |
| **8000** | `setuphelfer-backend.service` | FastAPI-Backend |
| **8080** | nginx (System) | **Kein** SetupHelfer — oft Ubuntu-Default-Seite |

## Browser-URLs

- **Haupt-UI:** http://127.0.0.1:3001/
- **Development Cockpit:** http://127.0.0.1:3001/?window=cockpit
- **API-Basis (Frontend-Default):** http://127.0.0.1:8000

## Profil

| Profil | `/api/dev-dashboard/status` | UI (`local_lab` Build) |
|--------|---------------------------|-------------------------|
| `release` | 404 `PROFILE_ROUTE_BLOCKED` | Cockpit deaktiviert (`devControlUiEnabled=false`) |
| `local_lab` | 200 (großes JSON) | Cockpit aktiv |

## Debugging (Browser)

1. F12 → **Network**
2. API-Calls müssen `127.0.0.1:8000/api/...` treffen
3. **Nicht** erwarten, dass `:3001/api/...` oder `:8080/api/...` das Backend ist

## Häufiger Irrtum

`curl -I http://127.0.0.1:8080/` zeigt `Server: nginx` → **kein DCC-Bug**, falscher Port.

Evidence: `docs/evidence/dev-dashboard/DCC_PORT_MAPPING_RESULT.md`
