# USB, Printer and Scanner Support — Rescue Stick

Status: PI-RS-HW-COMPAT-PROVISION-001 (Phase 19), extended by
PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 14).

Languages: [Deutsch](USB_PRINTER_SCANNER_SUPPORT_DE.md) · [English](USB_PRINTER_SCANNER_SUPPORT_EN.md) · [Français](USB_PRINTER_SCANNER_SUPPORT_FR.md) · [Nederlands](USB_PRINTER_SCANNER_SUPPORT_NL.md)

## USB device classification (`backend/core/usb_device_detection.py`)

Detected classes (minimum): mass storage, HID, keyboard, mouse, printer,
scanner, multifunction device, network adapter, Wi-Fi, Bluetooth, audio,
camera, serial adapters, smartcard, USB hub, external GPU (detection only),
`unknown`.

Sources: USB device class, interface classes, vendor/product ID,
udev properties, modalias, bound driver, present child interfaces.

### Multifunction devices

A composite device (e.g. printer+scanner+card reader) is modelled as
**one device with multiple independent capabilities**. Each function gets
its own `operational_status`. Setuphelfer never claims one function is ready
only because another function of the same device was detected.

## Printers (`backend/peripherals/printer_detection.py`, `printer_driver_resolver.py`)

Sources: USB Printer Class, IPP, IPP-over-USB, CUPS queues, `lpinfo` (if
present), mDNS/network discovery (if network is active), PPD metadata,
curated model catalogue.

Printer types: `matrix`, `inkjet`, `laser`, `thermal`, `label`, `unknown`.
Colour capability: `monochrome`, `color`, `unknown`.
Device kind: `printer`, `multifunction`, `scanner`, `fax_multifunction`,
`unknown`.

**Important:** print technology and colour capability are **not** guessed from
freely interpreted model names. Allowed sources are only: explicit IPP
capabilities, CUPS/PPD metadata, curated model catalogue, unambiguous vendor
information, tested fixtures. If data is unclear: `technology = unknown`,
`color_capability = unknown`, `classification_status = review_required`.

### Driver order

1. driverless IPP (if device and environment support it)
2. already present distribution driver
3. free generic driver
4. curated vendor package
5. proprietary driver — only as a clearly labelled option
6. `unsupported`/`review_required`

### Matrix / legacy devices

Parallel interfaces and USB-to-parallel adapters are detected without a
functionality guarantee. Generic ESC/P/PCL support is shown only as a
**candidate** — a physical print test remains required in every case.

## Scanners (`backend/peripherals/scanner_detection.py`, `scanner_driver_resolver.py`)

Sources: USB device data, `sane-find-scanner` (if present),
`scanimage -L` (if present), SANE backend information,
eSCL/AirScan (if present), network/MFP function.

Scanners and printers are **always verified separately**. No test print and
no scan is triggered without an explicit operator action — these modules
themselves never start print or scan jobs.

## Keyboards, mice and input devices (`backend/core/input_device_detection.py`)

Covered: USB keyboards/mice, Bluetooth input devices (only when already
connected), laptop keyboard, touchpad, trackpoint, touchscreen, generically
detected graphics tablets, gaming HID devices, KVM/composite devices.

### Strict privacy rule

- **no** recording of key presses
- **no** storage of mouse movements
- **no** keylogger-like tests
- Only existence, driver status and capability bits are captured.

## Physical evidence

All modules above have so far been tested only against synthetic
text/sysfs fixtures (`backend/tests/test_usb_device_detection_v1.py`,
`test_input_device_detection_v1.py`, `test_printer_detection_v1.py`,
`test_scanner_detection_v1.py`). See
`docs/evidence/rescue/hardware-compat-001/PHYSICAL_HARDWARE_TEST_MATRIX.md`
for the current (planned) physical verification status.
