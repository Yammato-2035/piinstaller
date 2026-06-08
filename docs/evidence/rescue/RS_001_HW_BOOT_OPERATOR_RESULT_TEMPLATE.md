# RS-001 HW Boot Operator Result

> **Vorlage** — vom Operator ausfüllen und als `RS_001_HW_BOOT_OPERATOR_RESULT.md` speichern.
> Cursor setzt RS-001 **nicht** auf grün, solange diese Datei nicht vollständig und belegbar ist.

---

## Metadata

- **Date:** YYYY-MM-DD
- **Operator:** `<Name/Kürzel>`
- **Repo HEAD:** `2fa3ea3` (oder aktueller HEAD nach Operator-Lauf)
- **ISO path:** `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso`
- **ISO SHA256:** `c9de3751f7fafe51c836d112bac99331c06252a01430b41f2a50b432ca63f194`
- **USB write method:** FAT32-ESP
- **USB device:** `<z. B. /dev/sdb>`
- **USB partition ESP:** `<z. B. /dev/sdb1 oder /dev/sdbp1>`
- **USB model:** `<aus lsblk MODEL>`
- **USB size:** `<aus lsblk SIZE>`
- **USB serial:** `<aus lsblk SERIAL, falls vorhanden>`

---

## Pre-write Device Check

### Vor dem Einstecken

```text
<Einfügen: lsblk -o NAME,PATH,SIZE,MODEL,TRAN,TYPE,FSTYPE,MOUNTPOINTS vor USB>
```

### Nach dem Einstecken

```text
<Einfügen: lsblk -o NAME,PATH,SIZE,MODEL,TRAN,TYPE,FSTYPE,MOUNTPOINTS nach USB>
```

### Operator-Bestätigung

```text
USB_DEVICE=
USB_SIZE=
USB_MODEL=
INTERNAL_DISKS=
CONFIRMED_NOT_INTERNAL=yes/no
```

**Pflicht:** `CONFIRMED_NOT_INTERNAL=yes` — sonst kein Write.

---

## ISO Pre-check

```text
<Einfügen: sha256sum Ausgabe>
```

Erwartet: `c9de3751f7fafe51c836d112bac99331c06252a01430b41f2a50b432ca63f194`

---

## ESP Layout Result

### Methode

- [ ] Repo-Skript: `write-fat32-esp-rescue-usb.sh --operator-confirm-write` + manuelle Schritte aus `write_manual`
- [ ] Manuell: parted + mkfs.vfat + rsync (siehe Phase-2-Runbook)

```text
<Einfügen: lsblk -o NAME,PATH,SIZE,MODEL,TRAN,TYPE,FSTYPE,PARTTYPENAME,MOUNTPOINTS nach ESP-Erstellung>
```

Erwartung:

- PTTYPE `gpt`
- Partition 1: `vfat`, PARTTYPENAME `EFI System` / `EF00`
- Label `SETUPHELFER` oder `SETUPHELPER` (je nach Methode)

---

## ESP Content Check

```text
<Einfügen: find/test Ausgabe>
```

Checkliste (alle **ja** für RS-001-Kandidat grün):

- [ ] `BOOTX64_OK`
- [ ] `GRUB_CFG_OK`
- [ ] `VMLINUX_OK`
- [ ] `INITRD_OK`
- [ ] `SQUASHFS_OK`

```text
test -f .../EFI/BOOT/BOOTX64.EFI && echo BOOTX64_OK
test -f .../boot/grub/grub.cfg && echo GRUB_CFG_OK
test -f .../live/vmlinuz && echo VMLINUX_OK
test -f .../live/initrd.img && echo INITRD_OK
test -f .../live/filesystem.squashfs && echo SQUASHFS_OK
```

---

## Hardware

| Feld | Wert |
|------|------|
| Manufacturer | |
| Model | |
| UEFI version | |
| Secure Boot | enabled / disabled |
| Boot mode | UEFI / Legacy / CSM |
| Fast Boot | enabled / disabled |
| USB boot enabled | yes / no |

Empfohlene Test-Einstellungen: Secure Boot **disabled**, UEFI **enabled**, Fast Boot **disabled**.

---

## UEFI Boot Result

| Prüfpunkt | yes / no |
|-----------|----------|
| USB shown in UEFI boot menu | |
| GRUB/Menu visible | |
| Kernel started | |
| Live system started | |
| Setuphelfer UI/TUI visible | |

**Error text / Fotobeschreibung:**

```text
<Fehlermodus: UEFI_MENU_NOT_VISIBLE | UEFI_ENTRY_VISIBLE_BUT_BOOT_FAILS | GRUB_VISIBLE_BUT_LINUX_FAILS | BOOT_SUCCESS>
<Details>
```

---

## MSI Compatibility Mode Result

| Feld | Wert |
|------|------|
| Tested | yes / no |
| Result | |
| Error text | |

Menüeintrag: „Setuphelfer MSI/NVIDIA-Kompatibilitätsmodus“ (`nomodeset`).

---

## Legacy Result

| Feld | Wert |
|------|------|
| Tested | yes / no |
| Stick visible | yes / no |
| Bootloader visible | yes / no |
| Result | |

Nur ausfüllen, wenn UEFI-Test fehlgeschlagen und Legacy verfügbar.

---

## Final Operator Assessment

| Feld | Wert |
|------|------|
| **RS-001 candidate status** | green / yellow / red |
| **Reason** | |
| **Evidence photos/logs** | Pfade oder „keine“ |
| **Next action** | |

### Status-Regeln (verbindlich)

**grün** nur wenn: FAT32-ESP erstellt, alle 5 ESP-Checks OK, UEFI sieht Stick, Bootloader+Kernel+Live+Setuphelfer-TUI sichtbar, keine manuelle Reparatur nach Boot.

**gelb** wenn: Stick erkannt, Bootloader/Kernel teilweise, Live scheitert eingrenzbar, oder nur MSI-Kompatibilitätsmodus funktioniert.

**rot** wenn: Stick unsichtbar, ESP fehlerhaft, Bootloader/Kernel startet nicht, oder Ergebnis unvollständig.

---

*Nach Ausfüllen: Datei als `RS_001_HW_BOOT_OPERATOR_RESULT.md` speichern und Entwicklung/Cursor zur Auswertung melden.*
