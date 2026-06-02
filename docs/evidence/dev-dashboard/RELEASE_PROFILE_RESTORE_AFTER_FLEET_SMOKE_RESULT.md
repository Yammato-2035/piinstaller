# Release-Profil Restore — Ergebnis

**Stand:** 2026-06-02  
**Status:** **blocked** (`release_restore_blocked_sudo_required`)

## Durchführung

| Schritt | Ergebnis |
|---------|----------|
| `sudo install … 92-install-profile-release.conf.example` | **nicht ausgeführt** — `sudo: Ein Passwort ist notwendig` |
| `systemctl daemon-reload` | nicht ausgeführt |
| `systemctl restart setuphelfer-backend.service` | nicht ausgeführt |

## Post-Restore (nicht gelaufen)

Keine Post-Restore-Gates oder API-Smokes nach Restore (STOP bei sudo-Block).

## Runtime unverändert

| Feld | Wert (weiterhin) |
|------|------------------|
| `install_profile` | `local_lab` |
| `dev_control_enabled` | `true` |
| `/api/dev-dashboard/status` | 200 |
| `/api/fleet/sessions` | 200 |

## Operator (freigegeben, manuelles Terminal)

```bash
cd /home/volker/piinstaller
sudo install -m 0644 \
  packaging/systemd/dropins/92-install-profile-release.conf.example \
  /etc/systemd/system/setuphelfer-backend.service.d/install-profile.conf
sudo systemctl daemon-reload
sudo systemctl restart setuphelfer-backend.service
./scripts/check-runtime-profile-deploy-gate.sh
curl -sS http://127.0.0.1:8000/api/version | jq '{install_profile, profile_gate_status, dev_control_enabled}'
curl -sS -i http://127.0.0.1:8000/api/dev-dashboard/status | head -8
curl -sS -i http://127.0.0.1:8000/api/fleet/sessions | head -8
```

Erwartung nach erfolgreichem Restore: `install_profile=release`, Dev/Fleet-API → `PROFILE_ROUTE_BLOCKED`.

## Nächster Lauf

Nach Operator-Restore: diese Datei auf **ok** aktualisieren oder `RELEASE_PROFILE_RESTORE_AFTER_FLEET_SMOKE_RESULT_POST_OPERATOR.md` anlegen.
