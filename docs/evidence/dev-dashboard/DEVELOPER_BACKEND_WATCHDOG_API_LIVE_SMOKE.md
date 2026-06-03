# Developer Backend Watchdog — API Live Smoke

**Datum:** 2026-06-03

## Durchführung

**Nicht ausgeführt** — Deploy blockiert (`deploy_exit=1`); local_lab-Profilwechsel ebenfalls sudo-pflichtig.

## Release-Baseline (Route in `/opt` nicht deployed)

`curl /api/dev-dashboard/backend-health` unter **release**:

- HTTP **404**
- `code`: **PROFILE_ROUTE_BLOCKED** (Middleware; Route noch nicht in `/opt/app.py`)

## Pflichtbewertung

| Feld | Wert |
|------|------|
| API HTTP 200 unter local_lab | **no** (nicht getestet) |
| current_health vorhanden | **no** |
| **Status** | **blocked** |

## Operator-Folge nach Deploy

```bash
sudo install -m 0644 packaging/systemd/dropins/92-install-profile-local-lab.conf.example \
  /etc/systemd/system/setuphelfer-backend.service.d/install-profile.conf
sudo systemctl daemon-reload && sudo systemctl restart setuphelfer-backend.service
sleep 3
curl -sS http://127.0.0.1:8000/api/dev-dashboard/backend-health | python3 -m json.tool
```
