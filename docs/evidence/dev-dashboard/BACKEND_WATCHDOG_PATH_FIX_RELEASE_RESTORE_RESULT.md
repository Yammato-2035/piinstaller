# Backend Watchdog Path Fix — Release Restore

**Datum:** 2026-06-03

| Feld | Wert |
|------|------|
| Release restore (Agent) | **nicht ausgeführt** (sudo; Runtime noch **local_lab**) |
| install_profile auf Disk | **local_lab** |
| **Status** | **review_required** |

## Operator (Pflicht vor QEMU)

```bash
sudo install -m 0644 packaging/systemd/dropins/92-install-profile-release.conf.example \
  /etc/systemd/system/setuphelfer-backend.service.d/install-profile.conf
sudo systemctl daemon-reload && sudo systemctl restart setuphelfer-backend.service
curl -sS http://127.0.0.1:8000/api/version | jq '{install_profile, dev_control_enabled}'
curl -sS -i http://127.0.0.1:8000/api/dev-dashboard/backend-health | head -20
```

Erwartung: `release`, `dev_control_enabled=false`, backend-health **404 PROFILE_ROUTE_BLOCKED**.
