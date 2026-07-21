# PI-RS-TUI-EVIDENCE-002 Final Report

Payload **1.10.0.60** was built via `payload_repack` from committed HEAD `6e96b7a4dfc311728e48c1852e341949ef6edfb5` and written to `/dev/sda` with the official FAT32 ESP updater after dual operator confirmations.

Post-write hashes for SquashFS/GRUB/Kernel/Initrd match the build. Persistence fix and shutdown gate are present in the squashfs. SETUP_LOGS and partition layout unchanged. MSI test not started.
