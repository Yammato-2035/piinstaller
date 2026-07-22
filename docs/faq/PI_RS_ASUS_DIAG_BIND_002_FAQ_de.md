# FAQ — ASUS Diag Bind 002 (DE)

1. **Why was an MSI session shown in the ASUS import?** A bug selected the newest session when boot_id did not match.
2. **How is mix-up prevented?** Boot-ID + manufacturer/board fingerprint gate.
3. **What is a Machine-Fingerprint?** Stable hash of DMI + optional PCI IDs without raw serials.
4. **Why is a timestamp not enough?** Different machines can boot the same stick on the same day.
5. **What does run_control_invalid mean?** Invalid for full_e2e/BVR; not required for hardware_discovery.
6. **Why is discovery not full E2E?** Different run-type contracts.
7. **Which NVMe values are stored?** Model, serial hash, EUI/NGUID, PCI path, SMART (when captured).
8. **Why hash serials?** Privacy in DCC/public reports.
9. **What do SMART values mean?** Health signals; critical_warning/media_errors can block install.
10. **Where are Windows setup logs?** Panther/Rollback on NTFS volumes (read-only).
11. **How is official BIOS checked?** ASUS Support only (G513QM page).
12. **Why no install yet?** Incomplete NVMe identity/SMART and missing Panther evidence.
