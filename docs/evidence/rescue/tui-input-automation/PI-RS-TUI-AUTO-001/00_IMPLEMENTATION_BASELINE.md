# 00 Implementation Baseline

Reuse:

- SETUP_LOGS: `core.rescue_setup_logs_resolver.resolve_setup_logs`
- GRUB lab patcher: `rescue_msi_lab_auto_boot.py` (append-only helper for diag)
- Payload carriers: `rescue_payload_version_carriers.py`
- Live install: `scripts/rescue-live/image` + inject glob `rescue_*.py`

Existing symptom evidence: PI-RS-INV-001 / PI-RS-TUI-INPUT-001 (menu visible, ~43% whiptail CPU).
