# Dev Agent — Rescue Developer Profile Integration

**Date:** 2026-05-30
**Agent base commit:** 0748492
**Branch:** main
**Runtime gate:** OK
**Dev-Server health:** enabled=true, mode=local_lab, storage_ok=true

## Profile paths

| Profile | Path |
|---------|------|
| Developer | `build/rescue/profiles/developer/` |
| Public guard | `build/rescue/profiles/public/` |

## Developer profile contents

- `manifest.json` — rescue_developer_local_lab, agent_enabled=true, local_lab
- `environment/setuphelfer-dev-agent.env` — ENABLED=true, AUTO_UPLOAD=true, SERVER=http://127.0.0.1:8000
- `systemd/setuphelfer-dev-agent.service` — EnvironmentFile, NoNewPrivileges, agent CLI only

## Public guard

- `SETUPHELFER_DEV_AGENT_ENABLED=false`
- `SETUPHELFER_DEV_AGENT_AUTO_UPLOAD=false`
- `SETUPHELFER_DEV_AGENT_MODE=public_rescue`

## Validation

```bash
./scripts/check-dev-agent-rescue-profile-guard.sh
# [GUARD] OK — exit 0

PYTHONPATH=backend:. python3 -m backend.devserver_agent.cli --validate-rescue-profile --json
# DEV_AGENT_RESCUE_PROFILE_OK
```

## Tests

```bash
cd backend && PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_devserver_agent_*' -v
# 54 OK
```

## Not performed

- No ISO build
- No lb build / chroot / debootstrap
- No USB write
- No hardware boot test
- No backup/restore

## Status

| Area | Status |
|------|--------|
| Profile integration | **GREEN** |
| Guard script | **GREEN** |
| Rescue ISO build | **pending** |
| Live boot agent | **pending** |
| Public/Beta production | **blocked/pending** |

## Next prompt

**RESCUE DEVELOPER ISO DRY-BUILD WITH DEV AGENT PROFILE GUARD**
