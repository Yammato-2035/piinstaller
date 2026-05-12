# Boot-Kompatibilität und Grenzen (Rescue / Phase 3.N7)

## Kontext-Erkennung

`detect_boot_context` im Zielbaum klassifiziert heuristisch:

- `raspberry_pi_firmware_boot` — `boot/firmware/config.txt`
- `x86_uefi` — `boot/efi/EFI`
- `x86_bios_legacy` — `boot/grub` vorhanden
- `unknown` — kein eindeutiges Muster

## Regeln

- **`unknown`**: keine automatische destruktive Boot-Reparatur (`rescue.boot.repair_not_supported`); es werden keine pauschalen GRUB-/chroot-Schritte „auf Verdacht“ ausgeführt.
- Alle Schreibaktionen nur mit `perform_boot_repair=true` und nur auf dem **extrahierten** Ziel-Root, nie auf dem laufenden Host-`/`.
- Raspberry Pi: Firmware-Dateien werden nur **gelesen** validiert; keine automatische Korrektur von `config.txt` / `cmdline.txt`.

## Grenzen

- UEFI vs. BIOS-Hybrid-Layouts können falsch klassifiziert werden.
- `grub-install` / `update-initramfs` setzen passende Tools und Root-Rechte im Ziel voraus — Fehler werden als `rescue.boot.repair_failed` gemeldet, nicht verschleiert.
- Echte Bootfähigkeit hängt von Firmware, Secure Boot, RAID und Hardware ab — Nachweis nur durch Zielhardware.
