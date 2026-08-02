# Rescue-Stick auf Raspberry Pi (arm64) — Machbarkeitsskizze

**Stand:** 2026-08-02 · **Status:** Architekturskizze, kein Code, kein Build

## Ist-Zustand (belegt)

Laut `docs/evidence/rescue/RESCUE_STICK_CAPABILITY_MATRIX.yaml`:

- `boot.arm64_uefi`: `planned` — kein `/live/arm64/`-Layout.
- `boot.raspberry_pi_3bplus`: `missing` — kein Rescue-Image, kein USB-Boot-/microSD-Shim-Konzept, USB-Boot bei Pi3B+ nicht voraussetzbar (Bootloader-EEPROM-Update nötig).
- `boot.raspberry_pi_4` / `boot.raspberry_pi_5`: `missing` — Pi ist im Projekt bisher **Installationsziel** der Hauptapp (`frontend/src/pages/RaspberryPiConfig.tsx`), nicht Rescue-**Boot**-Medium.

Der bestehende Rescue-Stick (`build/rescue/live-build/setuphelfer-rescue-live/`) baut ausschließlich `amd64` (`auto/config`, keine `--architectures`-Angabe). Das ist technisch und organisatorisch ein **eigener Build-Zweig**, keine Erweiterung des amd64-Sticks um ein paar Pakete.

## Grobskizze der nötigen Bausteine

1. **Zweiter live-build-Baum** mit `--architectures arm64` (oder komplett eigenständiger Build-Prozess, da Raspberry Pi klassischerweise nicht über GRUB/ISOLINUX bootet, siehe Punkt 2).
2. **Pi-spezifisches Boot-Layout statt GRUB/UEFI:** Raspberry-Pi-Firmware bootet über `config.txt`/`cmdline.txt` und `raspi-firmware`, nicht über die vorhandene `grub-efi`/`syslinux`-Kette (`scripts/rescue-live/patch-rescue-iso-uefi-x64.sh` ist x86-spezifisch und hier nicht anwendbar).
3. **Getrennte Kernel-/Firmware-Pakete:** `linux-image-arm64` statt `linux-image-amd64`; kein `intel-microcode`/`amd64-microcode` (Pi hat keine x86-CPU); Pi-spezifische Firmware/Bootloader-Dateien (`bootcode.bin`, `start*.elf`, `fixup*.dat`) kommen aus `raspi-firmware`, nicht aus den bestehenden `firmware-*`-Debian-Paketen.
4. **USB-Boot-Einschränkung Pi3B+:** ohne aktuelles Bootloader-EEPROM kein USB-Boot möglich — vor jedem Test zu prüfen, nicht pauschal voraussetzbar (bereits in der Capability-Matrix vermerkt).
5. **Eigener Evidence-/Testzyklus:** analog zum bestehenden MSI-Retest-Muster (`docs/test-plans/PI_RS_MSI_RETEST_*`) — mindestens ein physisches Gerät je Generation (Pi3B+, Pi4, Pi5), da sich Bootloader-Verhalten zwischen den Generationen unterscheidet.

## Ausdrücklich nicht Teil dieses Durchgangs

Kein Code, kein Build-Baum, keine Paketliste für arm64/Pi. Dieses Dokument ist eine
Grundlage für eine spätere, eigenständige Priorisierungsentscheidung — es ersetzt keine
Kapazitäts-/Prioritätsplanung und keinen physischen Testgeräte-Beschaffungsschritt.

## Verwandt

- `docs/knowledge-base/recovery/RESCUE_TARGET_ARCHITECTURES.md`
- `docs/architecture/RESCUE_TARGET_ARCHITECTURE_MATRIX.md`
- `docs/evidence/rescue/RESCUE_STICK_CAPABILITY_MATRIX.yaml`
- `docs/roadmap/RESCUE_HARDWARE_ASSESSMENT_ROADMAP.md`
