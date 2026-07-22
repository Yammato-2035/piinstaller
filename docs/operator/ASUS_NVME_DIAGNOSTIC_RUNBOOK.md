# ASUS NVMe Diagnostic Runbook

1. Boot GRUB **ASUS Hardwarediagnose (nur Lesen)**.
2. Confirm Gabriel phrase.
3. Capture writes under SETUP_LOGS `physical_runs/<run_id>/`.
4. Identity: serial_hash, EUI, NGUID, PCI — not `/dev/nvme0n1`.
5. No format/sanitize/write-zeroes.
