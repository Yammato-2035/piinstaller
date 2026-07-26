# AMD graphics stack audit (live Mint 22.2 casper)

## Kernel DRM

| Item | Status |
|------|--------|
| amdgpu.ko | present `.../drm/amd/amdgpu/amdgpu.ko.zst` |
| vermagic | `6.14.0-29-generic SMP preempt mod_unload modversions` |
| nouveau.ko | present (fallback path) |

## Firmware

| Item | Status |
|------|--------|
| `/lib/firmware/amdgpu` | **649** files in squashfs |

## Userspace (dpkg in live root)

- libdrm-amdgpu1 2.4.122-1~ubuntu0.24.04.1
- mesa-libgallium / mesa-vulkan-drivers 25.0.7-0ubuntu0.24.04.1
- xserver-xorg-core + xserver-xorg-video-amdgpu + modesetting via xserver-xorg-video-all
- nvidia-prime / nvidia-prime-applet present (userspace helpers)

## Gate vs Rescue cmdline

**amd_stack_in_image = passed**

**amd_stack_in_standard_rescue_boot = failed historically** because frozen Rescue GRUB used `nomodeset` + `amdgpu.modeset=0`.

Rebuild requirement: Hybrid Auto + AMD Safe profiles must **not** globally blacklist amdgpu or set nomodeset.
