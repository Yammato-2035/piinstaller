# ASUS ROG G513QM offline driver pack (Mint 22.2 / Ubuntu 24.04 noble)

Target machine: Gabriel — G513QM (Renoir iGPU + RTX 3060).  
Live kernel on stick casper: **6.14.0-29-generic** (Mint 22.2 Zara).  
Do **not** inject these debs into the live squashfs for GUI. Apply **after** base install (or via first-boot hook).

## Layout

```
g513qm/
  README.md
  MANIFEST.json
  debs/nvidia/          # nvidia-driver-550 + deps (.deb)
  debs/firmware/        # optional firmware debs
  config/modprobe.d/
  config/grub-profiles/
  scripts/apply-rog-pack.sh
  scripts/install-from-rescue.sh
```

## Operator order

1. Complete [`G513QM_OPERATOR_BIOS_GATE.md`](../../../../docs/evidence/rescue/install-assistant-001/G513QM_OPERATOR_BIOS_GATE.md).
2. Boot **Rescue-Root (Standard Gabriel)** only.
3. Run `scripts/install-from-rescue.sh` (no Cinnamon login).
4. After first boot of installed system: `scripts/apply-rog-pack.sh`.
5. Reboot with `postinstall-amd-igpu` profile; later enable NVIDIA profile if stable.

## FAT note

`SETUP_LOGS` is VFAT — execute bits may not stick. Always invoke:

```bash
bash /path/to/g513qm/scripts/install-from-rescue.sh
bash /path/to/g513qm/scripts/apply-rog-pack.sh --i-understand-no-windows-wipe
```

## NVIDIA package note

On Ubuntu 24.04 noble, `nvidia-driver-550` currently pulls the **580** driver stack (transitional metapackage). The slim pack contains those `.deb` files (~380 MB), not every cloud-kernel `linux-modules-nvidia-*` variant.
