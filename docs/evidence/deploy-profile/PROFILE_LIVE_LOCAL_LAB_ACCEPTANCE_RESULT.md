# Live-Abnahme Local-Lab-Profil

**Datum:** 2026-05-31 · **Evidence final:** nach Operator-sudo · **HEAD:** `eb47fe8`+

## Ergebnis: **grün** (Live + statisch)

| Flag | Wert |
|------|------|
| `local_lab_operator_sudo_completed` | **true** |
| `local_lab_dropin_set` | **true** |
| `local_lab_api_version_checked` | **true** |
| `local_lab_install_profile` | **local_lab** |
| `local_lab_fleet_sessions_enabled` | **true** |
| `local_lab_rescue_remote_enabled` | **true** |
| `local_lab_profile_gate_exit` | **0** |
| `local_lab_profile_gate_status` | **OK** |
| `dangerous_routes_visible` | **false** (keine rescue-remote shell/arbitrary/ssh; Security-Smoke) |
| `public_exposure_allowed` | **false** |
| `public_exposure_result` | **green** (Bind 127.0.0.1) |
| `remote_shell_disabled` | **true** |
| `write_runbooks_disabled` | **true** |
| `arbitrary_command_blocked` | **true** (403 `RESCUE_REMOTE_JOB_BLOCKED`) |

## Operator-Auszug (Live)

```text
install_profile: "local_lab"
fleet_sessions_enabled: true
rescue_remote_enabled: true
profile_gate: OK
check-runtime-profile-deploy-gate: OK (profile-aware, dev-dashboard independent)
```

## Release-Baseline vor Umschaltung

| Prüfung | Ergebnis |
|---------|----------|
| `install_profile` | `release` |
| Profil-Gate | **Exit 0** |

## Live-Umschaltung (systemd, Operator)

| Schritt | Ergebnis |
|---------|----------|
| Drop-in `92-install-profile-local-lab.conf.example` | **gesetzt** |
| `systemctl restart setuphelfer-backend.service` | **OK** |
| Profil-Gate | **Exit 0** |

### Durchgeführte Operator-Befehle

```bash
sudo cp packaging/systemd/dropins/92-install-profile-local-lab.conf.example \
  /etc/systemd/system/setuphelfer-backend.service.d/install-profile.conf
sudo systemctl daemon-reload
sudo systemctl restart setuphelfer-backend.service
./scripts/check-runtime-profile-deploy-gate.sh
```

## Nach Abnahme: Release wiederhergestellt

Siehe `PROFILE_LIVE_RELEASE_ACCEPTANCE_RESULT.md` — Runtime final: **release**.

## Statische Validierung (TestClient, ergänzend)

| Kriterium | Ergebnis |
|-----------|----------|
| `install_profile` | `local_lab` |
| OpenAPI: fleet / dev-diagnostics / rescue-remote | registriert |
| HTTP-Sonden (TestClient) | fleet, rescue-remote, dev-dashboard, dev-server **200** |
| Rescue-Remote: `shell` | **403**; read-only Job **200** |

## Public Exposure

- Bind: `127.0.0.1:8000`
- `public_exposure_allowed=false`

## Kein QEMU / ISO / USB / Backup / Restore / apt / Push
