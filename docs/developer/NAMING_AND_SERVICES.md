# Namensgebung und systemd-Dienste (Setuphelfer)

## Aktuelle Dienste (Zielbild)

| Unit | Rolle |
|------|--------|
| `setuphelfer-backend.service` | API (uvicorn), **alleiniger Owner** von TCP **:8000** |
| `setuphelfer.service` | Web-UI (Vite preview), **Requires** das Backend |

Vorlagen im Repo-Root: `setuphelfer-backend.service`, `setuphelfer.service` (Platzhalter `{{INSTALL_DIR}}` / `{{USER}}`). Debian-Paket: `debian/setuphelfer-backend.service`.

## Legacy (pi-installer)

Fruehere Releases nutzten u. a.:

- `pi-installer.service` / `pi-installer-backend.service`
- Installationspfad `/opt/pi-installer`

Diese Units sind **nicht** mehr Teil des aktiven Produktpfads, koennen auf migrierten Systemen aber noch existieren und **Port 8000** belegen. Setuphelfer erkennt das (siehe `docs/knowledge-base/diagnostics/SERVICE_CONFLICTS.md`).

## Umgebungsvariablen

Primär `SETUPHELFER_*`, kompatibel weiterhin `PI_INSTALLER_DIR` etc. (siehe `backend/core/install_paths.py`).

## API

- `GET /api/version` — Versionsstring der laufenden Instanz
- `GET /api/system/service-conflicts` — lesende Konflikt-/Port-Analyse
