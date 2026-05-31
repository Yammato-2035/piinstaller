# Dev Agent Server URL Resolution Contract

Version: 1.7.3.0

## Resolution order

1. CLI `--server http://...`
2. Environment `SETUPHELFER_DEV_AGENT_SERVER_URL`
3. Kernel cmdline `setuphelfer_dev_server_url=http://...` (when present)
4. QEMU user-NAT fallback `http://10.0.2.2:8000` when:
   - `mode=local_lab`
   - `SETUPHELFER_DEV_AGENT_QEMU_HOST_FALLBACK=true` or `--qemu-host-fallback`
   - health probe succeeds
5. Default `http://127.0.0.1:8000`
6. If no candidate reachable: **spool** (collect OK, upload deferred)

## Allowed hosts

- `127.0.0.1`, `localhost`, `::1`
- `10.0.2.2` (QEMU user NAT gateway)
- RFC1918 / link-local only

Public domains: **blocked**.

## Mode rules

| Mode | Auto-upload | QEMU fallback |
|------|-------------|---------------|
| `public_rescue` | never | never |
| `local_lab` | if enabled | optional explicit |
| `beta_opt_in` | opt-in only | not automatic |

## QEMU Developer Remote Access

- VNC bind: `127.0.0.1` only
- SSH hostfwd: `127.0.0.1` only, default **disabled**
- No `0.0.0.0`, no LAN/internet expose
- German keyboard: QEMU `-k de`, live `keyboard-layouts=de`

Implementation: `backend/devserver_agent/server_url.py`
