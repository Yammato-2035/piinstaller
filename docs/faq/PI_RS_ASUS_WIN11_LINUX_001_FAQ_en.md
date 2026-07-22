# FAQ — Firmware & Dual-NVMe Installation (EN)

1. **Does Setuphelfer flash BIOS automatically?** No.
2. **How is the correct BIOS known?** Official ASUS/MSI Support after high-confidence model ID.
3. **Why model + serial?** Device paths (`nvme0n1`) can swap across boots.
4. **Why not trust `/dev/nvme0n1`?** Linux names are unstable; use serial_hash + PCI + model.
5. **Which Windows logs?** Panther/Rollback setupact/setuperr and related.
6. **Why can Win11 abort on new NVMe?** Drivers, VMD/RST, media, RAM, firmware, UEFI/TPM — not only media health.
7. **What is Intel VMD/RST?** Storage modes that can hide NVMe from Windows Setup.
8. **Corrupt media?** Structure/SHA256 check → status `corrupt` blocks install.
9. **Why Windows before Linux?** Binding order + postcheck gate; Linux writes only after Windows OK.
10. **Why own Linux EFI?** Isolation; Windows ESP must not be Linux target.
11. **Is Windows NVMe changed by Linux install?** No — write blocked.
12. **What data is deleted?** Only the explicitly confirmed target NVMe after dual approval.
13. **Why confirm data loss again?** Safety against wrong-disk writes.
14. **Supported Linux?** Product: linux-mint; others experimental until tested.
15. **Why ISO checksum?** Prevent corrupt/tampered installer images.
