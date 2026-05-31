# Rescue Developer Dry-Build — Structure Scan

**Date:** 2026-05-31  
**HEAD:** e50f4b3  
**Scan type:** read-only structure analysis — **no build actions**

## Relevant paths found

### Developer / Public profiles

| Path | Purpose |
|------|---------|
| `build/rescue/profiles/developer/manifest.json` | Developer profile contract |
| `build/rescue/profiles/developer/environment/setuphelfer-dev-agent.env` | Agent env (local_lab) |
| `build/rescue/profiles/developer/systemd/setuphelfer-dev-agent.service` | ISO-target systemd unit |
| `build/rescue/profiles/public/manifest.json` | Public profile (agent disabled) |
| `build/rescue/profiles/public/environment/setuphelfer-dev-agent.env` | Public env (no auto-upload) |

### Packaging reference

| Path | Purpose |
|------|---------|
| `packaging/systemd/setuphelfer-dev-agent.service` | Host packaging template |

### Guard / validation

| Path | Purpose |
|------|---------|
| `scripts/check-dev-agent-rescue-profile-guard.sh` | Static profile guard (exit 0 = OK) |
| `backend/devserver_agent/rescue_profile.py` | Profile validation logic |
| `backend/devserver_agent/rescue_iso_dry_build.py` | ISO dry-build manifest (new) |
| `backend/devserver_agent/cli.py` | `--validate-rescue-profile`, `--rescue-iso-dry-build` |

### Dry-build / emulation (existing)

| Path | Purpose |
|------|---------|
| `build/rescue/emulation/rescue_stick_*.json` | Stick build previews (JSON only) |
| `build/rescue/debian-live/config_structure_manifest.json` | Live-build tree structure |
| `backend/deploy/runner_rescue_dry_build_orchestration.py` | Deploy-runner dry orchestration |
| `backend/deploy/runner_rescue_stick_readonly_build_emulation.py` | Read-only stick emulation |

### Prior live-build artifacts (existing/prior — not from this run)

| Path | Note |
|------|------|
| `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` | Prior controlled build |
| `build/rescue/live-build/.../filesystem.squashfs` | Prior artifact |
| `build/rescue/live-build/.../initrd.img`, `vmlinuz` | Prior kernel/initrd |

## Dry-build structure assessment

| Component | Status |
|-----------|--------|
| Developer profile tree | **present** |
| Public profile tree | **present** |
| Agent systemd in developer profile | **present** |
| Public agent disabled | **confirmed** |
| Emulation JSON previews | **present** |
| ISO dry-build manifest module | **implemented** (this run) |
| Real ISO build in this run | **no** |

## Developer-Agent profile files (materialization targets)

1. `environment/setuphelfer-dev-agent.env` → `/etc/setuphelfer/setuphelfer-dev-agent.env`
2. `systemd/setuphelfer-dev-agent.service` → `/etc/systemd/system/setuphelfer-dev-agent.service`
3. Spool: `/opt/setuphelfer/docs/evidence/runtime-results/dev-agent-spool`
4. Runtime module: `backend.devserver_agent.cli --send`

## Public profile status

- `agent_enabled=false`
- `AUTO_UPLOAD=false`
- `mode=public_rescue`
- Guard script exit **0**

## Risks

| Risk | Mitigation |
|------|------------|
| `deploy-to-opt.sh` copies dirty workspace | Clean HEAD worktree deploy (documented) |
| Prior ISO in `build/rescue/live-build` | Classified `existing_prior` in dry-build scan |
| Public auto-upload | Blocked by guard + manifest validation |

## Actions performed

- Structure scan only
- No lb build, debootstrap, chroot, squashfs, xorriso, USB write
