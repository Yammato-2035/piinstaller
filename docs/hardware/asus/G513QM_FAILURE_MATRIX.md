# G513QM Failure Matrix (Gabriel ASUS ROG Strix)

Machine: ROG Strix G513QM — Ryzen 7 5800H (AMD Renoir iGPU) + RTX 3060, Dual-NVMe.  
Stick: Intenso SETUPHELFER + SETUP_LOGS (`mint-live` casper).  
Policy: no BitLocker/Windows mutation; linux_target wipe only with phrase `WIPE LINUX TARGET`.

## 1. Own physical boots (2026-07-25 … 2026-07-26)

| Symptom | Boot profile | Likely cause | Countermeasure |
|---------|--------------|--------------|----------------|
| Hang at Mint Plymouth logo | Default casper `quiet splash` | Hybrid GPU + Plymouth | No splash; `noplymouth`; later Rescue path |
| Kernel text then black / “hang” at ASUS M-Key HID | Casper without pinned medium + `live-media-timeout=30` | Casper delayed scan; probes Windows NVMe | `live-media=/dev/disk/by-uuid/9BC7-3950`; `live-media-path=mint-live`; drop timeout |
| getty/CUPS OK, no usable console; login crashes | `multi-user.target` + `nomodeset` | Dead VT / display-manager path under hybrid | **Do not use multi-user as install path**; Rescue only |
| Keyboard hang | amdgpu allowed, no `nomodeset` | AMD KMS + ASUS HID interaction | Keep `nomodeset` for live/rescue; amdgpu only post-install profile |
| Kernel panic `exitcode=0x00000200` | `init=/bin/bash` | Broken early userspace for this casper | Never use emergency bash on Gabriel |
| **Stable text console** | **`rescue.target` + `nomodeset` + `gfxpayload=text` + pinned live-media** | Minimal services, text FB | **Frozen GRUB default** |

## 2. External reports (same class of hardware)

| Symptom | Source | Countermeasure in pack / process |
|---------|--------|----------------------------------|
| Mint/Ubuntu black screen after GRUB on ASUS gaming | [danielbrummitt.com](https://www.danielbrummitt.com/p/solving-the-linux-mint-black-screen) | `nomodeset` bypass for install; then proper drivers |
| Black screen after NVIDIA install on G513QM / RTX 30 | [AskUbuntu 1347461](https://askubuntu.com/questions/1347461/black-screen-after-installing-nvidia-driver-ubuntu-20-04-02-lts-rtx-30-series-o) | Match kernel↔driver; iGPU/`prime-select` style fallback; offline pack install after base OS |
| Soft-shutdown / broken keyboard on ROG after NVIDIA | Medium / NVIDIA forums / linux.org G513* | Prefer kernels ≥5.13; Mint 22.2 already newer; avoid live NVIDIA inject |
| ACPI / DPC stall / reboot freezes on Strix G | [ROG Forum BIOS Dec 2025](https://rog-forum.asus.com/t5/gaming-notebooks/linux-ubuntu-install-help-asus-bios-update-dec-2025-fixes-acpi/td-p/1134924) | **BIOS → G513QM.335** before next install (operator gate) |
| dGPU invisible under Linux | [asus-linux.org FAQ](https://asus-linux.org/faq/) | Windows Armoury Crate: dGPU **Auto** (not iGPU-only) |
| Dual-NVMe suspend delay (2021 G15) | [asus-linux.org FAQ](https://asus-linux.org/faq/) | Document for post-install; kernels ≥6.1 often fix; not blocking first install |
| Hybrid mode / nvidia sleep | [asus-linux.org guides](https://asus-linux.org/guides/arch-guide/) | Post-install: nouveau blacklist, nvidia-drm modeset, power services — via `apply-rog-pack.sh` |

## 3. Frozen supported path

1. GRUB: **Rescue-Root (Standard Gabriel)** only for physical work.
2. Offline pack: `SETUP_LOGS/setuphelfer/rog-pack/g513qm/`.
3. Install from Rescue without Cinnamon login (`install-from-rescue.sh`).
4. First boot: `apply-rog-pack.sh` → then `postinstall-amd-igpu` / later `postinstall-nvidia-prime`.

## 4. Explicitly unsupported on Gabriel live stick

- MSI Lab-Auto / Physical E2E as default
- Blind new kernel cmdline experiments without matrix update
- Injecting proprietary NVIDIA into live squashfs before base install
- Wipe/install on developer G713PI
