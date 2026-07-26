# Live base and kernel audit (Mint casper on SETUP_LOGS)

Source: loop-mounted `SETUP_LOGS/mint-live/filesystem.squashfs` + `vmlinuz` (read-only).

| Field | Value |
|-------|-------|
| base_distribution | Linux Mint |
| base_release | 22.2 |
| base_codename | zara (Ubuntu noble 24.04 family) |
| architecture | amd64 |
| kernel_package | (image in casper) linux 6.14.0-29-generic |
| kernel_version | 6.14.0-29-generic |
| linux_modules | present under `/lib/modules/6.14.0-29-generic` |
| linux_modules_extra | not separately audited as package name; modules tree present |
| linux_firmware | amdgpu firmware dir present (649 files counted) |
| mesa | mesa-libgallium / mesa-vulkan-drivers 25.0.7-0ubuntu0.24.04.1 |
| xorg | xserver-xorg-core 2:21.1.12-1ubuntu1.4 |
| installer_binary | `/usr/bin/ubiquity` |
| installer_package | ubiquity (present in live root) |
| nvidia_repository_origin | Ubuntu noble-updates/restricted (host apt used for offline pack) |
| offline_dependency_closure_status | nvidia-580 slim pack present; **not** live-kernel-module-complete |

## Implication

AMD DRM userspace + `amdgpu.ko` already in live image. Standard Rescue cmdline that sets `nomodeset` / `amdgpu.modeset=0` **disables** this stack for GUI.
