# Webserver Status Audit — G.7

**HEAD:** `a3e5825` · **Branch:** `main`

## Handler: `webserver_status` (vor G.7)

| Aspekt | Detail |
|--------|--------|
| Route | `GET /api/webserver/status` |
| Ort | `app.py` Z.8500–8581 (~82 Zeilen) |
| Frontend | `WebServerSetup.tsx` |

## Verantwortlichkeiten (vor Migration)

| Bereich | Implementierung | Owner vor G.7 |
|---------|---------------|---------------|
| Network-Info | `build_network_info()` | `network_info_facade` ✓ |
| Frontend-Port | `_detect_frontend_port()` | **app.py direkt** ✗ (G.5-Bypass) |
| Service-Status | `get_running_services()` | app (`systemctl is-active`) |
| Installierte Apps | `get_installed_apps()` | app |
| Port-Scan | `run_command("ss -tuln …")` | app |
| Website-Namen | `get_website_names()` | app (nginx/apache config parse) |
| CMS-Block | aus `get_installed_apps()` | app |

## Netzwerkanteil

- **1 Facade-Aufruf:** `build_network_info()`
- **1 Bypass:** `_detect_frontend_port()` — nicht über `network_info_facade`

## Webserveranteil

- nginx/apache installed+running
- mysql/mariadb/php
- cockpit/webmin (+ Port-Probes)
- `webserver_ports` (ss grep)
- `website_names`, `websites`, `installed_cms`

## Frontend-Port-Anteil

- `_detect_frontend_port`: `ss` auf 5173/3001/3002
- Verwendung in `pi_installer.port` und `pi_installer.url`

## Bestehende Bypässe (G.5)

| Bypass | Status G.7 |
|--------|------------|
| `webserver_status` → `_detect_frontend_port` | **beseitigt** → `network_info_facade.detect_frontend_port` |
| Handler-Logik in `app.py` | **beseitigt** → `webserver_status_facade.build_webserver_status` |

## Facade-Kandidat (umgesetzt)

`backend/core/webserver_status_facade.py` — `WEBSERVER_STATUS_FACADE_VERSION = 1`

### Legacy-Adapter (delegiert an app)

- `get_running_services`
- `get_installed_apps`
- `get_website_names`
- `run_command`
- `check_installed`

### Kanonische Facade-Nutzung

- `network_info_facade.build_network_info`
- `network_info_facade.detect_frontend_port`

## Response-Keys (unverändert)

`pi_installer`, `website_names`, `nginx`, `apache`, `mysql`, `mariadb`, `php`, `cockpit`, `webmin`, `network`, `webserver_ports`, `websites`, `installed_cms`
