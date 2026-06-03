# Runtime Ports — Frontend Live Review

**Datum:** 2026-06-03  
**DCC URL:** http://127.0.0.1:3001/?window=cockpit

## Ergebnisse

| Prüfung | Ergebnis |
|---------|----------|
| Port **3001** erreichbar | **yes** (HTTP 200, SimpleHTTP) |
| `/opt/setuphelfer/frontend/dist` aktuell | **yes** (Build 2026-06-03 12:25:27) |
| Port-/Profil-Hinweis im Bundle | **yes** — Strings `127.0.0.1:8000`, `127.0.0.1:3001`, Profil-/Block-Texte in `index-CBBG-uro.js` (minifiziert, grep-treffbar) |

Artefakte:

- `runtime_ports_frontend_3001_headers_latest.txt`
- `runtime_ports_frontend_dist_latest.log`
- `runtime_ports_frontend_bundle_scan_latest.log`

## Hinweis

Port **8080** (nginx) ist auf dem Host aktiv, gehört aber **nicht** zum SetupHelfer-DCC (`3001`).

## Status

**ok**
