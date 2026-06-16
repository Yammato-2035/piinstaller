# Payload Fix — Deploy Result

**Status:** `deployed` (Operator-Terminal, Pipeline fortgesetzt)

| Feld | Wert |
|------|------|
| `deploy_exit` | **0** (Operator: `sudo ./scripts/deploy-to-opt.sh`, Pipeline bis ISO+QEMU) |
| `/api/version` HTTP | **200** |
| `backend_runtime_path` | `/opt/setuphelfer/backend` |
| Fix-Marker in `/opt` | **yes** — `_profile_dev_server_defaults`, `require_token=False` unter local_lab, `lab_proxy_host_header_for_url`, `--print-payload`, `--dry-run` |

Evidence: `payload_fix_opt_backend_markers_latest.log`
