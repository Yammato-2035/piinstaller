# Windows 11 Post-Install Check Runbook

After successful install:

- Windows boots; OOBE or planned intermediate state
- ≥2 successful reboots
- System disk = Windows NVMe identity
- EFI on Windows NVMe
- Linux NVMe unchanged
- Device Manager / storage / Samsung NVMe
- Event Viewer: Disk, StorNVMe, WHEA, Kernel-Power, BugCheck
- Windows Update / chipset / ASUS drivers; NVIDIA only after stable base
- Secure Boot / TPM documented (no product keys)

Pass → `windows_postcheck_passed` → `linux_install_gate = ready_for_planning`  
Still no Linux write in this task.
