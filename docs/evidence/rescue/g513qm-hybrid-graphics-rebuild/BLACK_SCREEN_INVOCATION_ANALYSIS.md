# Black-screen invocation analysis

## Observed operator failure

Command:

```bash
bash /media/*/setuphelfer/rog-pack/g513qm/scripts/install-from-rescue.sh --mode ubiquity
```

Result: brief CLI text → full black screen → no reachable console → no visible installer → no live error display.

## Script behaviour (source audit)

File: `scripts/rescue/rog-pack-g513qm/scripts/install-from-rescue.sh` (pre-rebuild).

| Question | Finding |
|----------|---------|
| Installer command | `/usr/bin/ubiquity` via `startx /usr/bin/ubiquity` |
| Binary discovery | `command -v ubiquity` / `startx` only — no package query |
| Existing X session reused? | **No** — always starts new X |
| New X session? | **Yes** — `startx` |
| VT switch? | **Yes** if `openvt` exists: `openvt -s -w -- startx ...` (`-s` switches to new VT) |
| Existing X killed? | Not explicitly; Rescue has no X (rescue.target + DM masked) |
| User | root (sulogin) |
| DISPLAY / XAUTHORITY / DBUS / XDG_RUNTIME_DIR / HOME | **Not set** — relies on startx defaults as root |
| stdout/stderr durable log? | **No** |
| Can blacken screen without installer start? | **Yes** — `openvt -s` leaves Rescue TTY; `startx` under `nomodeset`/`amdgpu.modeset=0` can blank panel with failed modesetting |
| Capture independent of GUI? | **No capture at all** |
| Fallback text console on failure? | **No** |

## Boot context interaction

Frozen GRUB Rescue profile includes:

- `nomodeset`
- `amdgpu.modeset=0`
- `radeon.modeset=0`
- `modprobe.blacklist=nouveau,...`
- `systemd.unit=rescue.target`
- display-managers masked

So when `--mode ubiquity` calls `startx`, it asks Xorg for KMS/modesetting after the kernel cmdline **disabled** AMD KMS. That is a probable path to a black VT with no installer UI and no return to Rescue text.

## Classifications

| Class | Rating |
|-------|--------|
| `x11_handoff_failure` | **probable** (startx as root, no session reuse, openvt -s) |
| `vt_switch_failure` | **probable** (openvt -s leaves operator without Rescue TTY) |
| `display_manager_failure` | **excluded** (DM masked; not used) |
| `installer_process_failure` | **possible** (no process/log evidence from physical run) |
| `driver_failure_possible` | **possible** (nomodeset + amdgpu.modeset=0 makes GUI path hostile) |
| `driver_failure_confirmed` | **insufficient_evidence** (no dmesg/Xorg log from that run) |
| `secure_boot_nvidia_block` | **insufficient_evidence** / **unlikely** for this failure (proprietary NVIDIA not applied before ubiquity) |
| `insufficient_evidence` | for single root-cause claim |

**No single root cause confirmed.** Strongest combined hypothesis: Rescue graphics-disable cmdline + blind `startx`/`openvt -s` without capture/fallback.
