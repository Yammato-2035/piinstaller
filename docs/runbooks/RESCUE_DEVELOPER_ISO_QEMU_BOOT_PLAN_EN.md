# Rescue Developer ISO — QEMU Boot Plan (EN)

**Version:** 1.7.3.0
**Status:** Plan only — **do not run QEMU as part of this document**
**ISO run-ID:** `rescue_developer_iso_20260531_103047`

## Purpose

Controlled QEMU boot smoke test for the Rescue Developer Edition ISO as the next step after a successful controlled build.

## Prerequisites (met)

| Check | Status |
|-------|--------|
| Controlled ISO build LB_EXIT=0 | **yes** |
| ISO present | **yes** |
| SHA256 | `52da3e018ccbef827f8ad9bcccb9439c59e3131c501a21313d490f92a5c04326` |
| Developer profile / agent guard | **OK** |
| Public guard | **OK** |
| USB write | **not executed / blocked** |

## ISO path

```
build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso
```

Absolute: `/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso`

SHA256 file: `docs/evidence/runtime-results/rescue/rescue_developer_iso_latest.sha256`

## Host Dev Server URL (QEMU user NAT)

Inside the guest, `http://127.0.0.1:8000` is the **guest itself**, not the host.

| Context | URL |
|---------|-----|
| Hardware / host local | `http://127.0.0.1:8000` |
| QEMU guest → host (user NAT) | `http://10.0.2.2:8000` |

Developer-QEMU profile: `build/rescue/profiles/developer-qemu/`
Agent resolver: `--qemu-host-fallback` / `SETUPHELFER_DEV_AGENT_QEMU_HOST_FALLBACK=true`

**Option B (wrapper default):** host `socat` proxy `0.0.0.0:8001` → `127.0.0.1:8000`; guest URL `http://10.0.2.2:8001`.

**Option A (lab drop-in):** `scripts/rescue-live/apply-qemu-local-lab-backend-bind-dropin.sh` — see `docs/architecture/QEMU_HOST_DEV_SERVER_REACHABILITY_POLICY.md`.

## Agent module path (rescue runtime)

```bash
PYTHONPATH=/opt/setuphelfer-rescue \
  python3 -m backend.devserver_agent.cli \
  --mode local_lab --server http://10.0.2.2:8000 --send --json
```

Do **not** use `python3 -m devserver_agent.cli` with `PYTHONPATH=/opt/setuphelfer-rescue/backend` (ModuleNotFoundError).

Wrapper: `scripts/rescue-live/run-qemu-developer-iso-smoke.sh`
PID file: `docs/evidence/runtime-results/rescue/qemu/<RUN_ID>/qemu_gtk_pid.txt` (never `/qemu_gtk_pid.txt`)

## Remote access (local bind only)

- GTK console, local VNC `127.0.0.1:5901`, optional SSH forward `127.0.0.1:2222`
- No `0.0.0.0`, no public exposure
- Keyboard: `-k de`, locale `de_DE.UTF-8`

Guest read-only checks include `curl -s http://10.0.2.2:8000/api/dev-server/health` and agent send via `backend.devserver_agent.cli`.

## Planned QEMU command (baseline, do not execute in evidence-only run)

```bash
ISO_PATH="/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso"

qemu-system-x86_64 -m 2048 -smp 2 \
  -cdrom "$ISO_PATH" \
  -boot d -snapshot -no-reboot \
  -display gtk \
  -usb -device usb-tablet
```

## Optional serial log (for a later smoke run)

```bash
mkdir -p docs/evidence/runtime-results/rescue

qemu-system-x86_64 -m 2048 -smp 2 \
  -cdrom "$ISO_PATH" \
  -boot d -snapshot -no-reboot \
  -serial file:docs/evidence/runtime-results/rescue/qemu-serial-latest.log \
  -display gtk \
  -usb -device usb-tablet
```

## Acceptance criteria (future QEMU run)

1. ISO boots without kernel panic.
2. systemd is PID 1.
3. Setuphelfer Rescue runtime exists under `/opt/setuphelfer-rescue`.
4. Unit `setuphelfer-dev-agent.service` is present (enabled).
5. Agent sends only in **local_lab** mode to `http://127.0.0.1:8000`.
6. No USB writes, no dd, no target-device actions.
7. Dev server receives a report when host networking reaches the guest.
8. If networking is unavailable: spool under `/opt/setuphelfer-rescue/docs/evidence/runtime-results/dev-agent-spool`.

## Forbidden in QEMU smoke run

- USB passthrough to physical sticks
- `-hda` / `-drive` on `/dev/sd*`
- dd, mkfs, mount on host target devices
- backup/restore/verify deep
- apt install/upgrade on host

## Evidence after QEMU run (separate prompt)

- `docs/evidence/runtime-results/rescue/qemu-serial-latest.log`
- `docs/evidence/rescue/RESCUE_DEVELOPER_ISO_QEMU_BOOT_RESULT.md`
- Update `rescue_developer_controlled_iso_build_result.json` → `boot.boot_test_executed=true` only after a real boot

## References

- `docs/evidence/rescue/RESCUE_DEVELOPER_CONTROLLED_ISO_BUILD_RESULT.md`
- `docs/evidence/runtime-results/rescue/rescue_developer_iso_latest.sha256`
- `docs/runbooks/RESCUE_CONTROLLED_ISO_BUILD_RUNBOOK.md`
