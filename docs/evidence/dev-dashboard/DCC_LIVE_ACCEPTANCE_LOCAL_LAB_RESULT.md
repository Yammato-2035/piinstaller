# DCC Live Acceptance — local_lab Result

**Datum:** 2026-06-05  
**HEAD:** `c36b707`

## Status

**`dcc_profile_switch_blocked`**

## Profil/Runtime

* `install_profile` (live): `release`
* `dev_control_enabled` (live): `false`
* Backend läuft auf: `http://127.0.0.1:8000`

## Warum blockiert?

Ein `sudo`-Profilwechsel in dieser Agent-Session war nicht möglich:

```text
sudo: Ein Passwort ist notwendig
install_exit=1
```

Damit konnte `local_lab` nicht aktiviert werden und die Live-Akzeptanz für das DCC unter `local_lab` nicht ausgeführt werden.

## HTTP-Ergebnisse (statt local_lab)

| Endpoint | Expected (local_lab) | Tatsächlich (release) |
|---------|------------------------|------------------------|
| `/api/dev-dashboard/status` | 200 | 404 |
| `/api/dev-dashboard/backend-health` | 200 | 404 |
| `/api/dev-dashboard/recent-evidence` | 200 | 404 |
| `/api/fleet/sessions` | 200 | 404 |

Frontend-Cockpit ist an sich erreichbar:
* `http://127.0.0.1:3001/?window=cockpit` → 200
* aber DCC-Funktionalität bleibt unter release gesperrt (disabled page).

## Operator-Handoff (für echtes local_lab Live-Testen)

```bash
cd /home/volker/piinstaller

sudo install -m 0644 packaging/systemd/dropins/92-install-profile-local-lab.conf.example \
  /etc/systemd/system/setuphelfer-backend.service.d/install-profile.conf

sudo systemctl daemon-reload
sudo systemctl restart setuphelfer-backend.service
sleep 3

# Danach Phase C2 erneut ausführen (status/health/recent-evidence/fleet + Cockpit Headers)
```

## DCC-Sicherheitsbewertung

* Keine grüne DCC-Aussage, weil `local_lab` nicht live aktiviert werden konnte.
* USB bleibt weiterhin gesperrt (kein QEMU/Guest-Track in diesem Schritt).

