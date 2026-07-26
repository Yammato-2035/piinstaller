# Carrier update result

## Identity

- Matched unique USB: Intenso Ultra Line 59G serial 24111412110686
- Labels SETUPHELFER + SETUP_LOGS
- UUIDs 9BB9-A4A6 / 9BC7-3950
- Kernel name volatile (sdc observed); write used UUID mount

## Written

- `SETUP_LOGS/setuphelfer/rog-pack/g513qm/` (scripts, configs, nvidia-580 slim debs, MANIFEST pack_version 1.1.0)
- `SETUPHELFER/boot/grub/grub.cfg` — default Hybrid Auto
- Operator evidence tree under SETUP_LOGS/setuphelfer/operator/

## Gates

| Gate | Result |
|------|--------|
| package_dependency_closure (nvidia live module) | **failed** — headers for 6.14.0-29 unavailable |
| amd_stack_gate (image) | passed |
| nvidia_stack_gate (live proprietary vermagic) | **blocked_kernel_module_mismatch** |
| nvidia offline ABI single branch | passed (580) |
| grub_profile_validation | passed (unit tests) |
| capture scripts present | passed |
| carrier identity unique | passed |

Stick updated for **AMD Hybrid Auto physical retest** despite NVIDIA live-module blocker (documented).
