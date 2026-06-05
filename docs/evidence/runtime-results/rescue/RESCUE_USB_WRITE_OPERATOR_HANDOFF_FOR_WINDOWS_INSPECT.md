# Rescue USB Write — Operator Handoff (Windows Inspect)

**Status:** `uefi_x64_iso_ready_for_usb_operator_write`  
**Classification:** `uefi_x64_iso_ready_for_usb_operator_write`  
**Agent/Cursor:** **kein** automatisches `dd`

## ISO (UEFI-x64 validiert)

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| Größe | ~533 MiB (558891008 Bytes) |
| SHA256 | `09b9482a4ef18e2abf091edace794fc6baa27398f44b26e131db87ca855e0879` |
| UEFI Validator | Exit **0** — BIOS + EFI El Torito + BOOTX64 + efi.img |
| Erneuter UEFI-Patch | **nicht** ausführen, solange SHA256/Validator unverändert |

## Geräte — kritische Unterscheidung

| Gerät (Beispiel) | Größe | Rolle | Aktion |
|------------------|-------|-------|--------|
| `sda` | ~931G HGST USB | Backup-Disk | **NIEMALS** überschreiben |
| `sdb` | ~59G Ultra Line / INTENSO | möglicher Zielstick | **nur nach erneuter Prüfung** |
| `nvme0n1` / `nvme1n1` | interne NVMe | System | **NIEMALS** überschreiben |

Vor `dd`: `lsblk` **mit** und **ohne** Stick vergleichen. Nur die neu erschienene externe USB-Disk ist Kandidat.

## Warnung

```text
Dieser Vorgang löscht den Zielstick vollständig.
Nicht ausführen, wenn TARGET nicht eindeutig der USB-Stick ist.
```

## Operator-Kommandoblock

```bash
cd /home/volker/piinstaller

ISO=build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso

sha256sum "$ISO"
./scripts/rescue-live/validate-rescue-iso-uefi-boot.sh "$ISO"

lsblk -o NAME,SIZE,MODEL,SERIAL,TRAN,TYPE,MOUNTPOINTS

# Zielgerät manuell festlegen, Beispiel:
# TARGET=/dev/sdb
# ACHTUNG: TARGET muss der USB-Stick sein, nicht /dev/sda Backup, nicht NVMe.

echo "TARGET=$TARGET"
lsblk "$TARGET"

# Alle Partitionen des Zielsticks aushängen:
sudo umount "${TARGET}"?* 2>/dev/null || true

# ISO schreiben:
sudo dd if="$ISO" of="$TARGET" bs=16M status=progress conv=fsync

sync

# Nachkontrolle:
sudo blockdev --rereadpt "$TARGET" || true
lsblk -o NAME,SIZE,MODEL,SERIAL,TRAN,TYPE,MOUNTPOINTS "$TARGET"
sudo eject "$TARGET" || true
```

## Nach USB-Write

1. Stick am **MSI/Windows-11-Laptop** einstecken
2. UEFI-Bootmenü → USB/UEFI wählen (Secure Boot für Test aus)
3. Boot-Ergebnis dokumentieren
4. Erst dann: `docs/evidence/windows-rescue/WINDOWS11_RESCUE_STICK_BOOT_AND_INSPECT_HANDOFF.md`

## Blocker bis erledigt

- `RESCUE_STICK_NOT_WRITTEN`
- `RESCUE_USB_BOOT_NOT_VALIDATED_ON_TARGET`

**Next Prompt nach erfolgreichem MSI-Boot:** `WINDOWS11_RESCUE_OPERATOR_HARDWARE_READONLY_RUN`
