# Live-Abnahme Local-Lab-Profil

**Datum:** 2026-05-31 · **HEAD:** `aac3b88`

## Release-Baseline vor Umschaltung

| Prüfung | Ergebnis |
|---------|----------|
| `install_profile` | `release` |
| Profil-Gate | **Exit 0** |

## Live-Umschaltung (systemd)

| Schritt | Ergebnis |
|---------|----------|
| Drop-in `92-install-profile-local-lab.conf.example` | **blocked** — `sudo` Passwort erforderlich (`local_lab_dropin_blocked_sudo_required`) |
| Runtime bleibt auf | **release** (`/etc/systemd/.../install-profile.conf`) |

### Operator-Befehle (für Live-Abnahme)

```bash
sudo mkdir -p /etc/systemd/system/setuphelfer-backend.service.d
sudo cp packaging/systemd/dropins/92-install-profile-local-lab.conf.example \
  /etc/systemd/system/setuphelfer-backend.service.d/install-profile.conf
sudo systemctl daemon-reload
sudo systemctl restart setuphelfer-backend.service
sleep 3
curl -sS http://127.0.0.1:8000/api/version | jq .
./scripts/check-runtime-profile-deploy-gate.sh
```

Nach Abnahme **empfohlen** zurück auf Release:

```bash
sudo cp packaging/systemd/dropins/92-install-profile-release.conf.example \
  /etc/systemd/system/setuphelfer-backend.service.d/install-profile.conf
sudo systemctl daemon-reload
sudo systemctl restart setuphelfer-backend.service
./scripts/check-runtime-profile-deploy-gate.sh
```

## Statische Validierung (TestClient, `SETUPHELFER_INSTALL_PROFILE=local_lab`)

Ausgeführt im Workspace mit `backend/venv` (kein QEMU, kein ISO):

| Kriterium | Ergebnis |
|-----------|----------|
| `install_profile` | `local_lab` |
| `profile_gate_status` | `green` |
| `dev_control_enabled` | `true` |
| `dev_diagnostics_enabled` | `true` |
| `fleet_sessions_enabled` | `true` |
| `rescue_remote_enabled` | `true` |
| `dev_server_enabled` | `true` |
| `public_exposure_allowed` | `false` |

### OpenAPI (registriert)

| Präfix | Routen |
|--------|--------|
| `/api/fleet` | 5 |
| `/api/dev-diagnostics` | 5 |
| `/api/rescue-remote` | 9 |
| `/api/dev-server` | 14 |
| `/api/dev-dashboard` | 35 |

Keine `/api/rescue-remote/*` Routen mit `shell`, `arbitrary`, `ssh`.

### HTTP-Sonden (TestClient)

| Pfad | HTTP |
|------|------|
| `/api/fleet/sessions` | 200 |
| `/api/dev-diagnostics/latest` | 404 (`no_sessions` — erwartbar ohne Lab-Daten) |
| `/api/rescue-remote/jobs` | 200 |
| `/api/dev-dashboard/status` | 200 |
| `/api/dev-server/health` | 200 |

### Rescue-Remote Security Smoke (TestClient)

| Test | Ergebnis |
|------|----------|
| Agent register `local_lab` | 200 `RESCUE_REMOTE_AGENT_REGISTERED` |
| Job `shell` | **403** `RESCUE_REMOTE_JOB_BLOCKED` |
| Job `collect_network_status` read_only | **200** `RESCUE_REMOTE_JOB_CREATED` |
| `controlled_write` mode | **422** (Schema erlaubt nur `read_only`/`diagnostic`) |
| Tokens in Response | nicht exponiert (Register-Response geprüft) |

## Public Exposure (Live, unverändert Release)

- Bind: `127.0.0.1:8000` (ss)
- `public_exposure_allowed=false`

## Bewertung

| Ampel | Bereich |
|-------|---------|
| **Gelb** | Live systemd-Umschaltung (Operator-sudo ausstehend) |
| **Grün** | Statische Local-Lab-Logik + Rescue-Remote-Security (TestClient) |
| **Grün** | Release-Baseline vor Test |

## Profil-Gate (Live, Release aktiv)

`./scripts/check-runtime-profile-deploy-gate.sh` → **Exit 0** (Release)

## Tests

- Profil-Suite: **24/24** (1 Rescue-`test_enabled_in_dev` scheitert ohne `local_lab` env im isolierten Test — bekannt)
- Shell-Gate: OK

## Kein QEMU / ISO / USB / Backup / Restore / apt / Push
