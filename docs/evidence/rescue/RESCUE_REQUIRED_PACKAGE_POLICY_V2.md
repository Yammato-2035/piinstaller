# Rescue Required Package Policy V2

Policy-Datei: [`RESCUE_REQUIRED_PACKAGE_POLICY_V2.json`](./RESCUE_REQUIRED_PACKAGE_POLICY_V2.json)

## RS-011K / Master Phase 2

Alle Pflichtpakete für Hardware-/Firmware-/Treibererkennung sind in der Policy definiert und in `setuphelfer.list.chroot` (via `prepare-controlled-live-build-tree.sh`) abgebildet.

## Verboten

- `linux-modules-extra` (Ubuntu-spezifisch, nicht für Debian-Rescue-Liste)
- Ubuntu-spezifische Paketnamen

## Optional (review_required)

Malware/Security-Tools (`clamav`, `yara`, `lynis`, …) nur nach Lizenz- und Größenreview — nicht im Standard-Chroot.

## Backports-Kernel

Siehe [`RESCUE_BACKPORTS_KERNEL_DECISION_V2.md`](./RESCUE_BACKPORTS_KERNEL_DECISION_V2.md).
