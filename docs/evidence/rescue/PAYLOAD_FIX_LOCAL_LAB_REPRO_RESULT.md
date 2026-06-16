# Payload Fix — Local Lab Repro

**Status:** `local_lab_ready`

| Prüfung | Ergebnis |
|---------|----------|
| `local_lab` aktiv (vor QEMU) | **yes** |
| `dev_control_enabled=true` | **yes** |
| Devserver/Fleet HTTP 200 | **yes** — `DEVSERVER_PREFLIGHT_OK` |
| `require_token=false` | **yes** (Dropin + Config-Sync deployed) |
| Agent CLI `--print-payload`/`--dry-run` | **yes** |
| QEMU in dieser Phase | **no** |

Operator-Log: `DEVSERVER_PREFLIGHT_OK profile=local_lab dev_control=true fleet_http=200 dashboard_http=200`
