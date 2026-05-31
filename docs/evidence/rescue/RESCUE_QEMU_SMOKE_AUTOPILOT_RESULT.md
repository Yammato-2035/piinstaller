# Rescue QEMU Smoke Autopilot Result

**Date:** 2026-05-31
**HEAD Start:** e0e7bdb
**HEAD Ende:** (pending commit)
**Branch:** main
**Version:** 1.7.3.0

## Summary

| Field | Value |
|-------|-------|
| Status | **review_required** |
| Autopilot implemented | **yes** (profile + wrapper + tests) |
| New ISO built | **no** — preflight `blocked` (root-owned `.build/`) |
| Manual guest typing required | **no** (after new ISO) |
| QEMU autopilot run executed | **no** — blocked on ISO |

## Implementation

| Artifact | Path |
|----------|------|
| Architecture | `docs/architecture/RESCUE_DEVELOPER_QEMU_SMOKE_AUTOPILOT.md` |
| Guest script | `build/rescue/profiles/developer-qemu/includes.chroot/usr/local/sbin/setuphelfer-qemu-smoke-autopilot.sh` |
| systemd unit | `setuphelfer-qemu-smoke-autopilot.service` |
| Enable hook | `090-enable-qemu-smoke-autopilot.hook.chroot` |
| Host wrapper | `scripts/rescue-live/run-qemu-developer-iso-smoke.sh --autopilot` |
| Serial parser | `scripts/rescue-live/parse-qemu-serial-smoke-result.py` |

Prepare-tree verified: autopilot files + `console=ttyS0` in `auto/config`.

## Keyboard

- `/etc/default/keyboard`: `XKBLAYOUT="de"`
- Xsession: `setxkbmap -layout de -model pc105`
- Autopilot runs `loadkeys de-latin1` + `setxkbmap` at boot (no operator input)

## Proxy / Host

| Check | Value |
|-------|-------|
| Lab proxy | `0.0.0.0:8001` → `127.0.0.1:8000` |
| Guest URL | `http://10.0.2.2:8001` |
| Public auto-upload | **disabled** |
| SSH | **disabled** |

## ISO build blocker

```json
"status": "blocked",
"errors": ["root_owned_active_work_areas", "root_owned_top_level_artifacts"]
```

Operator fix:

```bash
cd /home/volker/piinstaller
sudo bash scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu ./scripts/rescue-live/prepare-controlled-live-build-tree.sh
./scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build --profile developer-qemu --run-id "<RUN_ID>"
```

Then:

```bash
scripts/rescue-live/run-qemu-developer-iso-smoke.sh \
  qemu_rescue_developer_autopilot_<TS> \
  --operator-confirm-qemu --autopilot --remote-vnc-local --keyboard de \
  --proxy-port 8001 --timeout-seconds 240
```

## Tests

| Suite | Result |
|-------|--------|
| `test_rescue_qemu_smoke_autopilot_profile_v1.py` | **10 OK** |
| Profile guard | **exit 0** |
| Runtime gates | **OK** |

## Safety

USB/dd/Backup/Restore/apt: **false**. No manual guest commands required once new ISO is booted.

## Next step

**FIX RESCUE DEVELOPER QEMU AUTOPILOT BOOT SERVICE** — after ISO rebuild, run `--autopilot` smoke and confirm Dev-Server report without typing.
