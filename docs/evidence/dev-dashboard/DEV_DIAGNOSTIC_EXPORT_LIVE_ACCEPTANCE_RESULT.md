# Dev Diagnostic Export — Live Acceptance

**Stand:** 2026-06-01  
**HEAD:** `ec0f8b6`  
**Branch:** `main`  
**Repository:** `Yammato-2035/piinstaller` (**PUBLIC**)  
**Push:** `no` (`push_blocked_public_repository_ndA_risk`)  
**NDA risk:** `blocked` (public repo)

## Zusammenfassung

| Kriterium | Ergebnis |
|-----------|----------|
| Vollständiger `deploy-to-opt.sh` | **nein** — `deploy_blocked_sudo_required` |
| Partieller Deploy (Gruppe `setuphelfer`) | **ja** — Backend-Module + `app.py`-Router + `frontend/dist` |
| Backend-Restart | **nein** — `sudo systemctl restart` benötigt Passwort |
| Live `:8000` `/api/dev-diagnostics/*` | **nein** (noch 404) — Prozess seit 09:48, Code auf Disk aktualisiert |
| Export-Logik auf `/opt` (TestClient) | **ja** — alle Pflichtwerte für `081222` |
| Frontend-Build | **ja** (`npm run build`) |
| Frontend nach `/opt` | **ja** (`index-BMMUHkh5.js`, Copy-Buttons im Bundle) |
| UI Browser | **pending** (Restart + manueller Browser) |

## Phase 0 — Gates vor Deploy

- `check-runtime-deploy-gate`: Exit **14** (Drift — erwartet vor Deploy)
- `check-backend-version-gate`: zuvor OK; Backend aktiv
- OpenAPI vor Deploy: **keine** `/api/dev-diagnostics/*`

## Phase 2 — Deploy

```text
sudo ./scripts/deploy-to-opt.sh → deploy_blocked_sudo_required (kein TTY-Passwort)
```

**Partiell (ohne sudo):**

- `/opt/setuphelfer/backend/core/dev_diagnostic_export.py`
- `/opt/setuphelfer/backend/dev_diagnostics/`
- `/opt/setuphelfer/backend/app.py` — Router-Registrierung ergänzt
- `/opt/setuphelfer/frontend/dist/` — Build `ec0f8b6` (inkl. `index.html` → `index-BMMUHkh5.js`)

## Operator-Aktion für Live-Abnahme

```bash
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller
sudo systemctl restart setuphelfer-backend.service
sleep 2
curl -sS http://127.0.0.1:8000/openapi.json | jq -r '.paths | keys[]' | grep dev-diagnostics
curl -sS "http://127.0.0.1:8000/api/dev-diagnostics/qemu-smokes/qemu_rescue_developer_autopilot_20260601_081222/export" | jq .
```

## TestClient-Abnahme (deployed Code, nicht :8000)

Aus `/opt/setuphelfer/backend` mit `SETUPHELFER_REPO_ROOT=/home/volker/piinstaller`:

| Feld | Wert |
|------|------|
| HTTP | 200 |
| `classification.primary` | `serial_empty_boot_unknown` |
| `serial_size_bytes` | `0` |
| `report_new` | `false` |
| `guest_found` | `false` |
| `redacted` | `true` |
| `sharing_warning` | vorhanden |

## OpenAPI / Control-Routen

- Live OpenAPI: **pending** (nach Restart)
- Keine Control-Routen im Router-Design (nur GET)

## Frontend UI (statisch)

Bundle `/opt/setuphelfer/frontend/dist/assets/index-BMMUHkh5.js` enthält:

- `lab-sessions`, `copySummary`, `copyJson`, `copyMarkdown`, `sharingWarning`, `dev-diagnostics`

## Redaction

Secret-Grep auf TestClient-Export: **kein Leak** (keine echten Keys in Evidence-JSON).

## Guardrails

- Kein QEMU, ISO, USB, Backup, Restore, apt, Push, öffentliches Deployment.

## Nächster Schritt

1. Operator: `sudo systemctl restart setuphelfer-backend.service` → Live-curl Phase 5 wiederholen.  
2. Browser: Development Control Center → Telemetry → Lab Sessions → Copy-Buttons.  
3. Dann: `FIX_RESCUE_ISO_SERIAL_CONSOLE_AND_BOOT_VISIBILITY`.
