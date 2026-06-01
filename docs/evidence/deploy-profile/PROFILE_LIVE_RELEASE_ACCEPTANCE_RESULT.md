# Live-Abnahme Release-Profil

**Datum:** 2026-05-31 · **Final:** nach Local-Lab-Rückschaltung

## Ergebnis: **grün**

| Kriterium | Status |
|-----------|--------|
| `/api/version` stabil | **yes** HTTP 200 |
| `install_profile` | **release** |
| `manifest_profile` | **release** |
| Dev-Capabilities | alle **false** |
| Forbidden-Routen HTTP | alle **404** |
| `check-runtime-profile-deploy-gate.sh` | **Exit 0** |
| Legacy-Gate | Exit **20** (informational only) |

## Nach Local-Lab: Release wiederhergestellt

| Flag | Wert |
|------|------|
| `release_restored_after_local_lab` | **true** |
| `release_install_profile` | **release** |
| `release_profile_gate_exit` | **0** |
| `release_profile_gate_status` | **OK** |
| `legacy_gate_non_profile_aware_exit_20_informational` | **true** |
| `dev_routes_release_blocked` | **true** |

### HTTP-Sonden (Release, final live)

| Pfad | HTTP |
|------|------|
| `/api/dev-dashboard/status` | **404** (erwartet) |
| `/api/fleet/sessions` | **404** |
| `/api/dev-diagnostics/latest` | **404** |
| `/api/rescue-remote/jobs` | **404** |
| `/api/dev-server/health` | **404** |

### Operator-Rückschaltung

```bash
sudo cp packaging/systemd/dropins/92-install-profile-release.conf.example \
  /etc/systemd/system/setuphelfer-backend.service.d/install-profile.conf
sudo systemctl daemon-reload
sudo systemctl restart setuphelfer-backend.service
./scripts/check-runtime-profile-deploy-gate.sh
```

## Local-Lab

Live-Abnahme **grün** — `PROFILE_LIVE_LOCAL_LAB_ACCEPTANCE_RESULT.md`.

## Historische Blocker (behoben)

- HTTP **000** nach Restart → Gate-Retries (`aac3b88`)
- `/api/dev-server/health` **200** im Release → `install_profile.py` ignoriert Dev-Overrides (`3ea1c69`)

## Kein QEMU / ISO / USB / Backup / Restore / apt / Push
