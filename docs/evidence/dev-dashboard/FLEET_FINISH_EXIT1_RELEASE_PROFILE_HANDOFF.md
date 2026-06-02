# Fleet / Lab — Release-Profil Handoff

**Stand:** 2026-06-02  
**Aktuelles Profil (gemessen):** `local_lab`  
**In diesem Lauf:** kein automatischer Profilwechsel

## Warum zurück auf release

- Produktivbetrieb ohne offene Dev-/Fleet-/Rescue-APIs
- DCC-UI nur mit `local_lab`-Frontend-Build; unter `release` bewusst deaktiviert
- ISO-Precheck / öffentliche Gates erwarten typisch `release`

## Operator-Befehle

```bash
cd /home/volker/piinstaller

sudo install -m 0644 \
  packaging/systemd/dropins/92-install-profile-release.conf.example \
  /etc/systemd/system/setuphelfer-backend.service.d/install-profile.conf

sudo systemctl daemon-reload
sudo systemctl restart setuphelfer-backend.service

./scripts/check-runtime-profile-deploy-gate.sh

curl -sS http://127.0.0.1:8000/api/version | jq '{install_profile, profile_gate_status, backend_runtime_path}'
curl -sS -i http://127.0.0.1:8000/api/dev-dashboard/status | head -8
curl -sS -i http://127.0.0.1:8000/api/fleet/sessions | head -8
```

## Erwartung nach Restore

| Prüfung | Ergebnis |
|---------|----------|
| `install_profile` | `release` |
| `/api/dev-dashboard/status` | **404** `PROFILE_ROUTE_BLOCKED` |
| `/api/fleet/sessions` | **404** `PROFILE_ROUTE_BLOCKED` |
| UI Cockpit | http://127.0.0.1:3001/?window=cockpit zeigt „nicht verfügbar“, wenn Frontend als `release` gebaut |

Optional Frontend für Produktion:

```bash
cd /opt/setuphelfer/frontend
sudo -u setuphelfer env SETUPHELFER_FRONTEND_BUILD_PROFILE=release npm run build
sudo systemctl restart setuphelfer.service
```

## Ports (unverändert)

- UI: **3001**
- API: **8000**
- **8080** = nginx, nicht SetupHelfer
