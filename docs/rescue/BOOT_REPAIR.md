# Boot-Reparatur auf dem Restore-Ziel (`rescue_boot_repair`, Phase 3.N7)

## Modularer Ablauf

| Schritt | Funktion | Rolle |
|---------|-----------|--------|
| 1 | `detect_boot_context` | `x86_uefi` \| `x86_bios_legacy` \| `raspberry_pi_firmware_boot` \| `unknown` |
| 2 | `validate_boot_artifacts` | Read-only: `analyze_boot_status` + Firmware-Hinweise |
| 3 | `choose_boot_repair_strategy` | Wählt erlaubte Teil-Schritte; bei `unknown` → keine destruktive Reparatur |
| 4 | `execute_boot_repair_if_allowed` | chroot-Binds (wenn nicht `dry_run`), optional `install_bootloader`, `update-initramfs` |
| 5 | `validate_boot_repair_result` | Mappt Fehler auf `rescue.boot.repair_failed` / `validation_uncertain` |

## Orchestrierung

`run_boot_repair_pipeline` führt die Schritte in dieser Reihenfolge aus und liefert `stages`, `boot_context` und `codes`.

## Plattformhinweise

- **x86**: GRUB über `restore_engine.install_bootloader` (Whole-Disk-Ziel).
- **Raspberry Pi**: typischerweise nur `initramfs_optional` ohne erzwungenes GRUB im aktuellen Modell.
- Details und Grenzen: `BOOT_COMPATIBILITY_LIMITATIONS.md`.

## Sicherheit

- Nur mit `perform_boot_repair=true` und nur auf dem **Ziel-Root**; `dry_run=true` unterdrückt alle Schreib- und Mount-Aktionen.
