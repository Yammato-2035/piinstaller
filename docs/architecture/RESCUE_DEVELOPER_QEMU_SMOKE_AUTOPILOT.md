# Rescue Developer QEMU Smoke Autopilot

**Version:** 1.7.3.0
**Status:** Lab automation — not a production default

## 1. Problem

- Manual typing in the QEMU guest is unreliable (wrong keyboard layout in X11).
- Host vs guest URL confusion (`127.0.0.1` vs `10.0.2.2:8001`).
- Smoke results were hard to reproduce and document.

## 2. Solution

| Component | Role |
|-----------|------|
| `setuphelfer-qemu-smoke-autopilot.sh` | Guest oneshot checks + agent send |
| `setuphelfer-qemu-smoke-autopilot.service` | systemd enable at `multi-user.target` |
| `run-qemu-developer-iso-smoke.sh --autopilot` | Host proxy, serial log, result JSON |
| `parse-qemu-serial-smoke-result.py` | Extract guest JSON from serial log |

Flow:

1. ISO boots (developer-qemu profile, `console=ttyS0`).
2. Autopilot runs without operator input.
3. Guest writes `/run/setuphelfer/qemu-smoke-result.json` and serial markers.
4. Host wrapper parses serial log + Dev-Server summary before/after.

## 3. Safety boundaries

- No USB, dd, backup, restore, mount, apt.
- No target-device writes.
- Public profile unchanged (no autopilot).
- Lab proxy `0.0.0.0:8001` → `127.0.0.1:8000` only during QEMU run.

## 4. Status logic

| Status | Criteria |
|--------|----------|
| `success` | Boot + systemd PID1 + rescue runtime + host health + agent send + host report |
| `review_required` | Autopilot ran; spool only or host report missing |
| `failed` | Runtime/agent missing or boot/autopilot not observed |
| `blocked` | Safety violation or ISO SHA mismatch |

## References

- `build/rescue/profiles/developer-qemu/`
- `docs/architecture/QEMU_HOST_DEV_SERVER_REACHABILITY_POLICY.md`
