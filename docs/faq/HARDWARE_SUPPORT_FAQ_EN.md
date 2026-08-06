# FAQ: Hardware Support (EN)

Short answers about the new hardware detection and provisioning layer
(PI-RS-HW-COMPAT-PROVISION-001). No marketing language.
Languages: [Deutsch](HARDWARE_SUPPORT_FAQ_DE.md) · [English](HARDWARE_SUPPORT_FAQ_EN.md) · [Français](HARDWARE_SUPPORT_FAQ_FR.md) · [Nederlands](HARDWARE_SUPPORT_FAQ_NL.md)

## Does Setuphelfer support my graphics card?

The GPU is detected and its state (driver bound, module loaded, firmware,
DRM device, active boot parameters such as `nomodeset`) is evaluated
separately. Whether display output actually works can only be confirmed by
a physical test — see
`docs/evidence/rescue/hardware-compat-001/PHYSICAL_HARDWARE_TEST_MATRIX.md`.

## Does the Rescue Stick automatically install NVIDIA/proprietary drivers?

No. Proprietary drivers are only shown as a **clearly labeled option**
(`driver_type: proprietary_optional`). They are never installed
automatically.

## What does "review_required" mean for the chipset?

The chipset is only named if the PCI ID, DMI data, or a curated catalog
entry allows a reliable match. If the data is insufficient, the system
honestly reports `review_required` instead of a guessed name.

## Can I use my printer/scanner right away?

The Rescue Stick shows whether a matching driver/backend is known and
offers a driver plan. An actual test print/scan is **not** triggered
automatically — that remains a deliberate operator action outside this
phase.

## Does Setuphelfer support all Raspberry Pi models equally?

No. Raspberry Pi 3, 3B+, 4, 400, CM4, Pi 5, and CM5 are individually
detected via device-tree data and each receive their own boot-medium and
OS-compatibility evaluation. Details:
`docs/rescue-stick/RASPBERRY_PI_3_TO_5_SUPPORT_EN.md`.

## Why doesn't the 64 GB stick simply contain every operating system?

Because space is limited. Setuphelfer uses an image catalog with signed
sources, checksums, and a bounded cache instead of a rigid "everything
included" image. Details: `docs/rescue-stick/64GB_CARRIER_ARCHITECTURE_EN.md`.

## Does this version already install operating systems?

No. `write_allowed` is always `false` for every provisioning plan in this
phase. No write operation is performed on real storage media.

## What data is sent to the cloud?

Only a redacted summary (platform class, CPU/GPU vendor, device counts per
status, kernel version, rescue payload version, issue codes). Serial
numbers, MAC/IP addresses, and full EDID data are never transmitted.
