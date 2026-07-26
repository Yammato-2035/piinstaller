# G513QM Control Result Decision Matrix

Physical outcomes drive status — never unit tests alone.

## Fall 1 — A ok, B ok, C freezes

`setuphelfer_boot_or_initramfs_fault_probable` → inspect Setuphelfer kernel/initramfs/modules/GRUB/debug services.

## Fall 2 — A ok, B freezes, C current-kernel ok

`kernel_6_14_regression_probable` → drop 6.14 from Setuphelfer live; pin supported kernel.

## Fall 3 — A/B freeze, C freezes on amdgpu load, nomodeset stable

`bios_acpi_amdgpu_or_hardware_fault_suspected` → BIOS-335 gate, HW diagnostics, netconsole, C2–C4 singles.

## Fall 4 — all Linux freeze + Windows/WinRE freeze + HW tools fail

`hardware_fault_highly_suspected` — **not** `hardware_defect_confirmed` without vendor/component proof.

## Fall 5 — internal black, external works, system alive

`internal_panel_display_path_suspected`

## Fall 6 — black screen, ping/SSH/netconsole alive

`display_stack_failure_not_full_system_crash`

## Fall 7 — netconsole shows amdgpu ring/timeout/reset

`amdgpu_gpu_hang_evidence_present` — needs further triage, not automatic HW condemnation.
