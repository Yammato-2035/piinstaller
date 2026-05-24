# Deploy — Rescue stick read-only build emulation (EN)

Read-only **emulation** for the SetupHelfer rescue stick: workspace snapshot, expected Debian live tree, package/bundle/systemd/network **previews**, evidence manifest, and final gate — **no** `lb build`, ISO, debootstrap, chroot, apt, mount, or qemu.

## Forbidden

No real build; no ISO/IMG/QCOW2/squashfs/initrd/vmlinuz under `build/rescue/`.

## Artifacts

See the German deploy doc `RESCUE_STICK_READONLY_BUILD_EMULATION_DE.md` for the file table (same paths).

## API (`POST`, prefix `/api/deploy`)

- `/rescue-stick/build-emulation/workspace-snapshot`
- `/rescue-stick/build-emulation/debian-live-tree`
- `/rescue-stick/build-emulation/package-list`
- `/rescue-stick/build-emulation/runtime-bundle`
- `/rescue-stick/build-emulation/frontend-bundle`
- `/rescue-stick/build-emulation/systemd-services`
- `/rescue-stick/build-emulation/network-webui`
- `/rescue-stick/build-emulation/evidence-manifest`
- `/rescue-stick/build-emulation/final-gate`
- `/rescue-stick/build-emulation/run-all`

## Response codes

`DEPLOY_RESCUE_STICK_BUILD_EMULATION_*_{OK|REVIEW_REQUIRED|BLOCKED}`; final gate: `DEPLOY_RESCUE_STICK_BUILD_EMULATION_FINAL_GATE_{READY|REVIEW_REQUIRED|BLOCKED}`.

## Tests

`backend/tests/test_deploy_runner_rescue_stick_readonly_build_emulation_v1.py`
