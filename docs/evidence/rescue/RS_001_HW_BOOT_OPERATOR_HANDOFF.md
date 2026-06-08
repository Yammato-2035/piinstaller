# RS-001 Hardware-Boot — Operator-Handoff

**Datum:** 2026-06-08  
**HEAD:** `669adb7`  
**Zweck:** Physischen UEFI-Boot vom Setuphelfer Rettungsstick auf Referenzhardware nachweisen (RS-001).  
**Cursor darf diesen Handoff nicht automatisch ausführen** — nur der Operator mit bewusster Geräteauswahl.

---

## 1. Zweck

RS-001 verlangt: **Debian Live bootet** auf Referenzhardware.  
Aktueller Stand: ISO-Artefakt ist strukturell UEFI/BIOS-fähig (Deep-Validator Exit 0), aber **MSI-Laptop bootete nicht** von isohybrid-dd-Stick trotz validiertem Readback.

Dieser Handoff bietet **zwei Pfade**:

- **Pfad A:** isohybrid-dd (bestehend, für QEMU/Lab bewährt)
- **Pfad B:** FAT32-ESP-GPT (empfohlen für MSI/UEFI-Realhardware)

---

## 2. ISO-Artefakt (kanonisch)

| Feld | Wert |
|------|------|
| Pfad (relativ) | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| Pfad (absolut) | `/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| SHA256 | `c9de3751f7fafe51c836d112bac99331c06252a01430b41f2a50b432ca63f194` |
| Größe | 683671552 Bytes (~652 MiB) |
| Projektversion Workspace | `1.7.9.0` |

**Vor Write prüfen:**

```bash
cd /home/volker/piinstaller
sha256sum build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso
# Muss exakt c9de3751f7fafe51c836d112bac99331c06252a01430b41f2a50b432ca63f194 sein
```

Falls SHA abweicht: zuerst Operator-Rebuild (siehe Abschnitt 8).

---

## 3. Erwartete Stick-Größe

- Minimum: **≥ 1 GiB** (ISO ~652 MiB)
- Empfohlen: **≥ 8 GiB** für FAT32-ESP-Layout (SquashFS + ESP + Puffer)
- Referenz-Testgerät bisher: Ultra Line 59G (`/dev/sdb`, Serial dokumentieren)

---

## 4. Geräteprüfung vor USB-Write (Pflicht)

```bash
# 1) Stick einstecken, dann:
lsblk -o NAME,SIZE,TYPE,TRAN,VENDOR,MODEL,SERIAL,MOUNTPOINTS
# 2) Stick wieder abziehen, erneut lsblk — nur der neue Eintrag ist der Stick
# 3) Seriennummer und Größe notieren
# 4) Sicherstellen: Stick ist NICHT /dev/sda wenn das die Systemplatte ist
```

**Abbruch wenn:**

- Gerätename unsicher
- Stick gemountet (`MOUNTPOINTS` nicht leer) — erst `umount`
- Größe passt nicht zum physischen Stick

---

## 5. Pfad A — isohybrid-dd (klassisch)

### USB-Write (nur mit bewusst gesetztem Gerät)

```bash
# NICHT blind ausführen. <USB_DEVICE> bewusst ersetzen (z. B. /dev/sdb).
ISO="/home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso"
USB_DEVICE="<USB_DEVICE>"

# Sicherheitscheck
lsblk "$USB_DEVICE"
read -r -p "Wirklich $USB_DEVICE überschreiben? tippe GERÄTENAME: " CONFIRM
test "$CONFIRM" = "${USB_DEVICE##*/}"

sudo dd if="$ISO" of="$USB_DEVICE" bs=4M status=progress conv=fsync
sync
sudo partprobe "$USB_DEVICE" || true
```

### Readback-Verify

```bash
ISO_SIZE=$(stat -c%s "$ISO")
sudo dd if="$USB_DEVICE" of=/tmp/usb_readback_head.img bs=1 count="$ISO_SIZE" status=none
sha256sum "$ISO" /tmp/usb_readback_head.img
# Hashes müssen identisch sein
```

### UEFI-Struktur nach Write (read-only)

```bash
sudo lsblk -f "$USB_DEVICE"
sudo file -s "${USB_DEVICE}1" 2>/dev/null || true
# Erwartung isohybrid: PARTTYPE 0x17, FSTYPE iso9660, Label SETUPHELFER_RESCUE
```

---

## 6. Pfad B — FAT32-ESP (MSI-empfohlen)

### Dry-Run (ohne Write)

```bash
cd /home/volker/piinstaller
./scripts/rescue-live/write-fat32-esp-rescue-usb.sh \
  --iso build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso \
  --target <USB_DEVICE> \
  --dry-run
```

### Plan ohne Write (nur Vorbereitung)

```bash
export USB_DEVICE=/dev/sdb   # bewusst setzen — nie blind kopieren

./scripts/rescue-live/write-fat32-esp-rescue-usb.sh \
  --iso build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso \
  --target "$USB_DEVICE" \
  --operator-confirm-write \
  --confirm-phrase "WRITE SETUPHELFER FAT32 ESP USB"
```

Ohne `--execute-write`: nur Plan + `write_manual`; `write_executed=false`; **kein** destruktiver Write.

### Destructive Write (Operator-Terminal only)

```bash
export USB_DEVICE=/dev/sdb   # bewusst setzen

./scripts/rescue-live/write-fat32-esp-rescue-usb.sh \
  --iso build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso \
  --target "$USB_DEVICE" \
  --operator-confirm-write \
  --confirm-phrase "WRITE SETUPHELFER FAT32 ESP USB" \
  --execute-write
```

**Wichtig:**

- `--execute-write` ist **destruktiv** (wipefs, sgdisk, mkfs, rsync).
- Die Bestätigungsphrase allein reicht **nicht** mehr — `--execute-write` ist zusätzlich Pflicht.
- **Cursor/DCC führt diesen Befehl nicht aus** — nur der Operator im physischen Terminal.
- Evidence: `docs/evidence/runtime-results/rescue/fat32_esp_write_<timestamp>/` + `fat32_esp_write_latest.json`
- RS-001 bleibt **rot**, bis HW-Boot bis Setuphelfer-Menü/TUI nachgewiesen ist.

Verify nach Write:

```bash
./scripts/rescue-live/verify-fat32-esp-rescue-usb.sh --target "$USB_DEVICE"
```

**Erwartung nach Write:**

- GPT mit Partition 1: `EF00` FAT32, Label `SETUPHELFER`
- `EFI/BOOT/BOOTX64.EFI` auf ESP
- Live-Artefakte auf Datenpartition

Verify:

```bash
./scripts/rescue-live/validate-rescue-iso-uefi-boot.sh build/.../binary.hybrid.iso  # ISO weiterhin
# Stick: sudo blkid ${USB_DEVICE}1 — TYPE=vfat, PARTLABEL=SETUPHELFER_RESCUE
```

Dokumentation: `docs/evidence/runtime-results/rescue/RESCUE_USB_FAT32_ESP_LAYOUT_PROTOTYPE.md`

---

## 7. UEFI-Boot-Test auf Referenzhardware

1. Alle anderen USB-Sticks entfernen
2. UEFI-Bootmenü öffnen (oft F11/F12/DEL — gerätespezifisch)
3. **UEFI:** Eintrag für USB / „UEFI: <Stickname>“ wählen
4. Beobachten und **exakt** dokumentieren:

| Fehlermodus | Operator trägt ein |
|-------------|-------------------|
| `UEFI_MENU_NOT_VISIBLE` | Stick erscheint nicht im Bootmenü |
| `UEFI_ENTRY_VISIBLE_BUT_BOOT_FAILS` | Eintrag da, schwarzer Bildschirm / sofort zurück |
| `GRUB_VISIBLE_BUT_LINUX_FAILS` | GRUB-Menü sichtbar, Kernel-Panic oder Hänger |
| `BOOT_SUCCESS` | Live-System / Start Assistant sichtbar |

5. Bei MSI: auch Menüpunkt **„Setuphelfer MSI/NVIDIA-Kompatibilitätsmodus“** testen (`nomodeset`)

### BIOS/Legacy (optional, falls Gerät nur Legacy)

- Im Firmware-Setup Legacy/CSM aktivieren
- Boot-Reihenfolge USB-HDD/Legacy
- ISOLINUX-Menü „Setuphelfer Rettungsstick“ erwarten

---

## 8. ISO-Rebuild (falls nötig)

Nur wenn Workspace-Änderungen auf Stick sollen oder SHA nicht passt:

```bash
cd /home/volker/piinstaller
./scripts/rescue-live/prepare-controlled-live-build-tree.sh   # ggf. Operator
./scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build
./scripts/rescue-live/validate-rescue-iso-uefi-boot.sh build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso
```

**Hinweis:** Erfordert sudo/root im Operator-Terminal.

---

## 9. Rückmeldung an Entwicklung (Pflicht)

Operator liefert:

1. **Pfad** (A isohybrid oder B FAT32-ESP)
2. **USB_DEVICE** (z. B. `/dev/sdb`) + Serial + Größe
3. **SHA256** nach Write/Readback
4. **Fehlermodus** aus Tabelle (Abschnitt 7)
5. **Foto/Screenshot** Bootmenü (optional)
6. **Serial-Log** falls vorhanden (UART-Debug)
7. **Firmware:** UEFI only / Legacy / Secure Boot an/aus
8. Ergebnis RS-001: `BOOT_SUCCESS` ja/nein

Evidence ablegen:

- `docs/evidence/rescue-stick/RS-1.json` aktualisieren
- Kurzbericht: `docs/evidence/rescue/RS_001_HW_BOOT_OPERATOR_RESULT.md` (vom Operator)

---

## 10. Abbruchkriterien

- Gerätename unsicher → **STOP**, kein dd
- Readback-SHA ≠ ISO-SHA → **STOP**, Stick nicht testen
- Interne Systemplatte (`nvme0n1`, `/dev/sda` mit Root-FS) → **niemals** Ziel
- Stick enthält andere wichtige Daten → **STOP** ohne Backup

---

## 11. Destruktive Aktionen

**Verboten ohne explizite Gerätebestätigung:**

- `dd`, `wipefs`, `sgdisk`, `mkfs`, `parted write`

**Erlaubt read-only:**

- `lsblk`, `blkid`, `file`, `sha256sum`, ISO-Mount read-only, Validator-Skripte

---

## 12. MSI-Triage-Kurzfassung

Bisheriger MSI-Test (ISO `3fe6628a...`):

- USB-Readback = ISO (**ja**)
- Deep-UEFI-Validator (**ja**)
- Laptop bootet (**nein**)
- Wahrscheinliche Ursache: **isohybrid 0x17**, kein FAT-ESP `0xEF`

**Nächster sinnvoller Versuch auf MSI:** Pfad B (FAT32-ESP).

---

*Erstellt in Phase 1 HW-Boot. Kein automatischer Write durch Cursor.*
