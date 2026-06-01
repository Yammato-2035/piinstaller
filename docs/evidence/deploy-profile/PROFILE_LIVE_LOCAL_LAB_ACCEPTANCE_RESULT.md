# Live-Abnahme Local-Lab-Profil

**Datum:** 2026-05-31

## Status

**Nicht umgeschaltet** in diesem Lauf (Release-Profil aktiv auf Live-Runtime).

## Operator-Schritte

```bash
sudo cp packaging/systemd/dropins/92-install-profile-local-lab.conf.example \
  /etc/systemd/system/setuphelfer-backend.service.d/install-profile.conf
sudo systemctl daemon-reload && sudo systemctl restart setuphelfer-backend
./scripts/check-runtime-profile-deploy-gate.sh
```

## Erwartung

- `/api/fleet`, `/api/dev-diagnostics`, `/api/dev-dashboard` HTTP **2xx**
- Keine Shell-/Write-Routen unter `/api/rescue-remote`
- Profil-Gate Exit **0**
