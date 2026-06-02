# Development Control Center — Port Mapping

**Generated:** 2026-06-02T17:23:43+00:00  
**HEAD (Workspace):** `d3baeca`

## Erwartete Zuordnung

| Port | Dienst | Bedeutung |
|-----:|--------|-----------|
| 3001 | SimpleHTTP / SetupHelfer static SPA (`setuphelfer.service`) | SetupHelfer UI / Development Cockpit |
| 8000 | uvicorn / FastAPI (`setuphelfer-backend.service`) | Backend / API |
| 8080 | nginx (Ubuntu) | **Nicht** SetupHelfer — Default-/Separat-Webserver |

## URLs

| Zweck | URL |
|-------|-----|
| Haupt-UI | http://127.0.0.1:3001/ |
| Development Cockpit | http://127.0.0.1:3001/?window=cockpit |
| Backend / API | http://127.0.0.1:8000/ |

## Live Checks (2026-06-02)

```text
$ curl -sS -I http://127.0.0.1:3001/ | head -5
HTTP/1.1 200 OK
Server: SimpleHTTP/0.6 Python/3.12.3

$ curl -sS -I http://127.0.0.1:8080/ | head -5
HTTP/1.1 200 OK
Server: nginx/1.24.0 (Ubuntu)

$ curl -sS http://127.0.0.1:8000/api/version | jq '{install_profile, dev_control_enabled}'
install_profile: local_lab
dev_control_enabled: true
```

## Entscheidung

- Port **8080** wird **nicht** als SetupHelfer Development Control Center bewertet.
- DCC-UI-Smokes: Port **3001** (Browser).
- API-Smokes: Port **8000** (`/api/dev-dashboard/*`, `/api/fleet/*`, …).
- Requests in F12 → Network müssen nach `http://127.0.0.1:8000/api/...` gehen, **nicht** `:3001/api/...` oder `:8080/api/...` (statischer SPA-Server auf 3001 liefert für `/api/*` nur 404-Hinweis).
