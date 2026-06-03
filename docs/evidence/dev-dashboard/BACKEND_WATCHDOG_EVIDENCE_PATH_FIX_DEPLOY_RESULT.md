# Backend Watchdog Evidence Path Fix — Deploy Result

**Datum:** 2026-06-03

| Feld | Wert |
|------|------|
| Deploy (Agent) | **blocked** (`sudo` Passwort) |
| Deploy Exit | **1** |
| `/opt` Evidence chmod 664 (manuell/Healthcheck) | **yes** |
| `/opt` latest JSON mit `repo_root=/opt/setuphelfer` | **yes** |
| `/opt` Loader-Code aktualisiert | **no** — Operator-Deploy ausstehend |

## Operator

```bash
cd /home/volker/piinstaller
sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller
/opt/setuphelfer/scripts/dev-dashboard/check-backend-health.sh
```

| Feld | Wert |
|------|------|
| **Status** | **review_required** (Deploy + API-Smoke) |
