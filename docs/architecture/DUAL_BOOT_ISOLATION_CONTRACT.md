# Dual Boot Isolation Contract

## Goals

- Each NVMe preferably independently bootable.
- Linux ESP only on Linux NVMe.
- Windows Boot Manager preserved; Windows ESP not used as Linux target.
- Firmware boot menu is primary selector; GRUB→Windows optional, not required.
