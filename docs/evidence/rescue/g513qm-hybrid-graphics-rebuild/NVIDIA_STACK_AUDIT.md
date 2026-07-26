# NVIDIA stack audit

## 550 → 580 clarification

On Ubuntu noble apt, `nvidia-driver-550` is a **transitional metapackage** that depends on `nvidia-driver-580`. The slim offline pack therefore contains ABI **580** libraries (`libnvidia-*-580`, `nvidia-dkms-580`, …) plus the tiny `nvidia-driver-550` transitional deb.

**Rule going forward:** pack metapackage pin = `nvidia-driver-580` only (single ABI branch). Drop reliance on 550 naming in manifests.

## Live kernel module match

| Check | Result |
|-------|--------|
| Live kernel | 6.14.0-29-generic |
| `linux-headers-6.14.0-29-generic` in apt | **not available** (madison empty) |
| Prebuilt `linux-modules-nvidia-580-6.14.0-29-generic` | **not found** |
| Closest prebuilt | other 6.14.0-* flavours / hwe-7.0 — **wrong vermagic** |
| `modinfo nvidia` in live root | **absent** (no proprietary module in squashfs) |
| Nouveau in live | **present** |

## Gate

```text
nvidia_live_proprietary_vermagic = blocked_kernel_module_mismatch
nvidia_offline_pack_abi = 580_single_branch_slim
nvidia_postinstall_path = pack_apply_on_installed_system
nouveau_fallback_live = available
```

## PRIME userspace in live

`nvidia-prime` / `nvidia-prime-applet` packages present; without proprietary module, PRIME offload cannot be claimed ready.

## Secure Boot

Detect-only; unsigned proprietary module must not break AMD Safe boot.
