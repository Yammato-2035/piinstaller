# Carrier Update 1.10.6.0 — PENDING OPERATOR DUAL CONFIRM

## Target carrier (from prior campaigns)

- Device class: Intenso Ultra Line USB
- Expected serial (prior): `24111412110212`
- Labels: `SETUPHELFER` + `SETUP_LOGS`
- Preserve: `SETUP_LOGS` evidence

## Planned writes (after dual confirm only)

1. SquashFS → ESP/live `filesystem.squashfs`
2. GRUB cfg with default `ASUS-TUI-BASELINE-HIGHINFO`
3. Manifest / version metadata
4. Readback verify SHA256

## Required confirm phrases (operator)

Confirm **twice**, explicitly naming device identity and payload `1.10.6.0`, before any USB write.

## Not authorized yet

- Internal NVMe writes
- Windows EFI changes
- Linux installation
