# Linux Second NVMe Install Contract

**Module:** `rescue_linux_second_nvme.py`

## Rules

- Windows postcheck must pass first.
- Distro explicit (`TARGET_LINUX_DISTRO`); missing → `ready_for_distro_selection`.
- First product support mark: `linux-mint` supported; others experimental.
- ISO SHA256 required for install authorization.
- Layout: ESP 1 GiB on Linux NVMe only, root, home remaining, swapfile.
- Bootloader → `linux_nvme_esp_only`.
- Windows NVMe `write_allowed=false` always during Linux path.
- `install-execute` requires dual confirmation + preflight TTL + serial/machine match; returns handoff, no silent wipe.
