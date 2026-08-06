# Hardware Compatibility Model — Rescue Stick

Status: PI-RS-HW-COMPAT-PROVISION-001 (Phase 19), extended by
PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 14).

Languages: [Deutsch](HARDWARE_COMPATIBILITY_MODEL_DE.md) ·
[English](HARDWARE_COMPATIBILITY_MODEL_EN.md) ·
[Français](HARDWARE_COMPATIBILITY_MODEL_FR.md) ·
[Nederlands](HARDWARE_COMPATIBILITY_MODEL_NL.md)

## Core statement

**Detection is not a guarantee of function.** For every device, the rescue
stick shows a traceable, multi-level status instead of a single yes/no
statement.

## Status traffic light (Rescue UI)

| Light | Meaning |
|---|---|
| 🟢 Green | detected, driver loaded, firmware present, device operational |
| 🟡 Yellow | detected, but limited / optional driver / physical test required / capability not fully verified |
| 🔴 Red | driver missing, firmware missing, kernel incompatible, device blocked, safe activation not possible |
| ⚪ Gray | unknown, not checked, tool missing, no reliable classification |

This traffic light is implemented in `frontend/src/rescue/RescueHardwarePanel.tsx`
and `frontend/src/rescue/rescue-shell.css` (`.rescue-hw-badge-*`). The
separate hardware baseline diagnostics (RAM/CPU/GPU/storage) use an
analogous but independent traffic light — see
`HARDWARE_BASELINE_DIAGNOSTICS_EN.md`.

## Covered hardware classes

1. CPUs and SoCs (`backend/core/cpu_platform_detection.py`)
2. GPUs/graphics paths (`backend/core/gpu_detection.py`, `gpu_driver_resolver.py`)
3. Mainboards and chipsets (`backend/core/mainboard_chipset_detection.py`)
4. PCI/PCIe devices (`backend/core/hardware_inventory.py::collect_pci_devices`)
5. USB devices (`backend/core/usb_device_detection.py`)
6. Mass storage/controllers (`hardware_inventory.py::collect_storage_controllers`)
7. Network adapters (`hardware_inventory.py::collect_network_devices`)
8. Keyboards/mice (`backend/core/input_device_detection.py`)
9. Printers (`backend/peripherals/printer_detection.py`)
10. Scanners (`backend/peripherals/scanner_detection.py`)
11. Raspberry Pi 3–5 (`backend/platforms/raspberry_pi_*.py`) — see
    `RASPBERRY_PI_3_TO_5_SUPPORT_EN.md`
12. Multi-arch provisioning preparation — see
    `MULTI_ARCH_PROVISIONING_MODEL_EN.md`

## Architecture rule: no hard-coded mass catalog

Thousands of devices are **not** hard-coded in source. Instead:

```
Hardware IDs/system information
  → normalized HardwareDevice (backend/core/hardware_contracts.py)
  → generic driver/firmware resolution (backend/core/driver_resolver.py)
  → small curated compatibility database for special cases
    (data/hardware/hardware_compat_catalog.json)
  → safe activation planning (backend/core/driver_activation_plan.py, preview-only)
  → traceable verification (evidence references, physical test matrix)
```

## Driver and firmware resolution

Driver/firmware resolution (`backend/core/driver_resolver.py`,
`backend/core/driver_activation_plan.py`) follows the same order for every
detected device class:

1. driver already present in the running kernel/distribution
2. free, generic driver from the standard repository
3. curated vendor package (`data/hardware/hardware_compat_catalog.json`)
4. proprietary driver — only as a clearly labeled option that requires
   manual confirmation (`driver_type: proprietary_optional`)
5. `unsupported`/`review_required` if none of the above levels apply

Firmware follows the same principle: presence is detected and assessed,
absence is reported — an automatic firmware activation or automatic
firmware download does **not** happen in this development phase. Every
activation plan (`driver_activation_plan.py`) is exclusively a preview
(`preview-only`), never an executed write or installation action.

## Example: multifunction device

An "HP multifunction device" is modeled as **one device with several
capabilities**, not as a single blanket "works" status:

```
Device: HP multifunction device
Functions:
  - printer   → own operational_status
  - scanner   → own operational_status
  - storage_card_reader → own operational_status
```

It is **never** claimed that the scanner works just because the print
function was detected.

## Proprietary drivers

Proprietary drivers (e.g. the full NVIDIA module) are presented as an
**optional candidate** (`driver_type: proprietary_optional`), never
installed automatically. Every proprietary option requires a separate,
manual review by the operator.

## Next phase

Real driver installation, firmware activation, printer/scanner functional
tests and physical Raspberry Pi boot tests are only covered in
`PI-RS-HW-ACTIVATE-002`.
