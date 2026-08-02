# Rescue Hardware Assessment Roadmap

1. **V2 (this phase):** Automated assessment, issue/recommendation codes, redaction
2. **Next:** Integrate assessment into rescue UI + telemetry upload dry-run on stick boot
3. **Next:** Hardware DB population from approved telemetry exports only
4. **Future:** Firmware package recommendations per hardware_key
5. **Done (2026-08):** Firmware/microcode package coverage in `setuphelfer.list.chroot`
   synced with `RESCUE_REQUIRED_PACKAGE_POLICY_V2.json` (`intel-microcode`,
   `amd64-microcode`, `lshw`, `hwinfo`, `nvme-cli` etc.); `parted`/`ntfs-3g`
   deliberately kept out (still forbidden by `validate-live-build-dpkg-preflight.sh`
   pending a write-safety gate). Peripheral discovery (`rescue_peripheral_discovery.py`)
   and driver-catalog lookup (`driver_catalog.py`) added to `system-assessment.v2`,
   see `docs/knowledge-base/rescue/DRIVER_CATALOG_AND_PERIPHERAL_DISCOVERY.md`.
   **Not** claimed: verified boot/detection on any hardware beyond the existing
   evidence trail — this is code coverage, not a hardware test result.
6. **Open, hardware-dependent (not started):** i386 build tree, Legacy-BIOS
   physical boot evidence, Secure Boot shim signing — each needs its own
   physical-device evidence cycle per `RESCUE_STICK_CAPABILITY_MATRIX.yaml`,
   not just code.
7. **Open, separate initiative (not started):** Raspberry Pi (arm64) rescue-boot
   image — see `docs/architecture/RESCUE_ARM64_RASPBERRY_PI_BOOT_FEASIBILITY.md`
   for the feasibility sketch. This is a new build track, not an extension of
   the existing amd64 rescue stick.
