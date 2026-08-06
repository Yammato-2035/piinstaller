# Raspberry Pi 3 to 5 — Support Model

Status: PI-RS-HW-COMPAT-PROVISION-001 (Phase 19), extended by
PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 14).

Languages: [Deutsch](RASPBERRY_PI_3_TO_5_SUPPORT_DE.md) ·
[English](RASPBERRY_PI_3_TO_5_SUPPORT_EN.md) ·
[Français](RASPBERRY_PI_3_TO_5_SUPPORT_FR.md) ·
[Nederlands](RASPBERRY_PI_3_TO_5_SUPPORT_NL.md)

## Core statement

**There is no blanket statement "Raspberry Pi 3–5 supported".** Every
combination of board, architecture, operating system, boot medium and
image version is assessed individually:

```
Board × architecture × operating system × boot medium × image version × test status
```

Raspberry Pi 3 can have architecture, memory and boot requirements that
differ from Raspberry Pi 5.

## Covered platform families

- Raspberry Pi 3 / 3B+
- Raspberry Pi 4
- Raspberry Pi 400
- Compute Module 4 (as far as generically detectable via device tree)
- Raspberry Pi 5
- Compute Module 5 (only if reliably detectable in the current stack)

## Modules

| Module | Purpose |
|---|---|
| `backend/platforms/raspberry_pi_detection.py` | Exact model detection via `/proc/device-tree/model`, `/proc/device-tree/compatible`, SoC info, RAM size |
| `backend/platforms/raspberry_pi_boot_plan.py` | Boot medium support (microSD, USB mass storage, NVMe on Pi 5, network boot as `future/experimental`) |
| `backend/platforms/raspberry_pi_compatibility.py` | Compatibility summary per model |
| `backend/platforms/raspberry_pi_os_plan.py` | Matrix of OS candidates per model/RAM/architecture |

## Detection sources

- `/proc/device-tree/model`, `/proc/device-tree/compatible`
- SoC information and architecture (`aarch64`/`armv7`)
- Boot medium
- EEPROM/bootloader status — **read-only**, no modification
- RAM size
- Network interfaces, WiFi/Bluetooth status
- USB controllers, storage, PCIe/NVMe (Pi 5)
- HAT/overlay information, where detectable
- Camera/display interfaces — detection only, no activation

## Status values

- `boot_supported`
- `bootloader_update_recommended`
- `bootloader_update_required`
- `storage_supported`
- `os_compatible`
- `physical_validation_required`

## Operating system matrix (preparation)

| Category | Support status |
|---|---|
| Raspberry Pi OS | current catalog entry (see `data/provisioning/os_catalog.json`) |
| Debian ARM64 | current catalog entry |
| Ubuntu Server ARM64 | current catalog entry |
| Ubuntu Desktop ARM64 | optional |
| further systems | `future`/`unsupported` |

## Serial number/privacy

Serial numbers are **only handled redacted locally**, never transmitted in
plain text. Any device binding uses exclusively a stable, salted hash —
never a raw value.

## No EEPROM change in this phase

Bootloader/EEPROM status is **read-only**. An EEPROM update is not part of
this phase and remains reserved for `PI-RS-HW-ACTIVATE-002`.

## Physical evidence

The current modules have been tested against synthetic device tree
fixtures (`backend/tests/test_raspberry_pi_detection_v1.py`,
`test_raspberry_pi_os_compatibility_v1.py`). A physical test run against
real boards is still pending — see
`docs/evidence/rescue/hardware-compat-001/PHYSICAL_HARDWARE_TEST_MATRIX.md`.
No model may be labeled "verified" without physical evidence.
