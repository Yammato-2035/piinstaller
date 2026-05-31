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

## Planned QEMU command (do not execute in evidence-only run)

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
