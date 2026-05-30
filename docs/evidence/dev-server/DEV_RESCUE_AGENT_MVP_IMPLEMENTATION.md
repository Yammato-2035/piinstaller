# Development Rescue Agent — MVP Implementation Evidence

**Date:** 2026-05-30
**Base commit:** `806ce08` (Development Server MVP)
**Branch:** `main`
**Runtime gate:** OK

## Agent modules

| Component | Path |
|-----------|------|
| Config | `backend/devserver_agent/config.py` |
| Collector | `backend/devserver_agent/collector.py` |
| Redaction client | `backend/devserver_agent/redaction_client.py` |
| HTTP client | `backend/devserver_agent/client.py` |
| Spool | `backend/devserver_agent/spool.py` |
| CLI | `backend/devserver_agent/cli.py` |
| systemd helper | `backend/devserver_agent/systemd.py` |
| systemd template | `packaging/systemd/setuphelfer-dev-agent.service` |

## Modes

| Mode | Auto-upload |
|------|-------------|
| public_rescue | blocked (default) |
| beta_opt_in | explicit + redaction |
| local_lab | allowed when AUTO_UPLOAD=true |

## Collector (read-only allowlist)

Hardware: uname, lscpu, free, hostnamectl, os-release
Storage: lsblk, findmnt, blkid
Boot: UEFI/BIOS, mokutil, efibootmgr, /boot listing
Rescue runtime: systemctl is-system-running, ps, ip, date

Forbidden: sudo, mount, dd, mkfs, parted, apt, rm, systemctl start/stop/restart

## Tests

```bash
cd backend && PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_devserver_agent_*' -v
# 40 tests OK

cd backend && PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_devserver_*' -v
# 84 tests OK (7 skipped)
```

## Runtime smoke (live Development Server)

```bash
SETUPHELFER_DEV_AGENT_ENABLED=true \
SETUPHELFER_DEV_AGENT_MODE=local_lab \
SETUPHELFER_DEV_AGENT_AUTO_UPLOAD=true \
SETUPHELFER_DEV_AGENT_SERVER_URL=http://127.0.0.1:8000 \
SETUPHELFER_DEV_AGENT_NODE_ID=agent-smoke-node \
SETUPHELFER_DEV_AGENT_DISPLAY_NAME="Agent Smoke Node" \
PYTHONPATH=/home/volker/piinstaller/backend:/home/volker/piinstaller \
python3 -m backend.devserver_agent.cli --send --json
```

**Result:** GREEN

| Field | Value |
|-------|-------|
| code | DEV_AGENT_UPLOAD_OK |
| dev server code | DEV_SERVER_REPORT_ACCEPTED |
| node_id | agent-smoke-node |
| report_id | report-d83b73c520e842c3 |
| redaction_status | raw_lab |
| report_type | rescue |

**Summary after smoke:** node_count=2, reports_last_24h=2

Warnings (expected local_lab): sensitive serial/uuid fields flagged in summary, not blocked.

## Storage paths

- Dev server (runtime): `/opt/setuphelfer/docs/evidence/runtime-results/dev-server/`
- Agent spool: `docs/evidence/runtime-results/dev-agent-spool/`

## Security

- Default disabled
- Public auto-upload blocked
- No SSH
- No write/backup/restore routes in agent
- Token not logged
- Server URL restricted to localhost/private LAN in MVP

## Status

| Area | Status |
|------|--------|
| Agent code + tests | GREEN |
| Agent runtime smoke | GREEN |
| Public/Beta production use | pending/blocked |
| Rescue ISO integration | pending |
| Signed runbooks | pending |
| Adaptive profiles | pending |
| Backup-gated remote actions | blocked/future |

## Next prompt

**INTEGRATE DEV AGENT INTO RESCUE DEVELOPER EDITION PROFILE**
