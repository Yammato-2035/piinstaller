# DCC — Release Restore After Recovery

**Datum:** 2026-06-03

| Feld | Wert |
|------|------|
| Release-Restore (Agent) | **nicht ausgeführt** (sudo Passwort) |
| API während Smoke | `local_lab` |
| `install-profile.conf` auf Disk | `release` (Dropin-Datei) |
| Effektives API-Profil | noch `local_lab` (laufender Dienst ohne Agent-Restart) |

**Erwartung nach Operator-Restore:**

```bash
sudo systemctl daemon-reload
sudo systemctl restart setuphelfer-backend.service
# install-profile.conf bereits release laut Disk-Stand
```

`/api/dev-dashboard/recent-evidence` → dann `PROFILE_ROUTE_BLOCKED` unter release.

**Status:** `review_required` (Release-Trap durch Operator abschließen)
