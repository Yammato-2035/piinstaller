# Raspberry Pi 5: Vollständiger Boot von der NVMe (ohne SD-Karte)

**Erstellt:** 2026-02-23  
**Zweck:** System von SD-Karte auf NVMe überspielen und so konfigurieren, dass der Pi 5 **ausschließlich von der NVMe** startet. Zusätzlich Speicher-Optimierung für den 8 GB Pi.

---

## 1. Übersicht

| Modell | Beschreibung |
|--------|--------------|
| **Hybrid-Boot** (bisher) | Boot-Partition auf SD, Root auf NVMe – siehe `docs/PATHS_NVME.md`, Clone in PI-Installer |
| **Vollboot NVMe** | Boot und Root auf NVMe; SD-Karte kann danach entfernt werden |

Nach dem hier beschriebenen Vorgang:

- **Boot-Partition** und **Root** liegen auf der NVMe.
- Die **Boot-Reihenfolge** im EEPROM wird auf „NVMe zuerst“ gestellt.
- Der **Speicher** kann für den 8 GB Pi sinnvoll genutzt werden (Swap, optional zram).

---

## 2. Voraussetzungen

- **Raspberry Pi 5** mit **NVMe** (z. B. M.2-HAT+ oder kompatibler PCIe-Adapter).
- Aktuelles **Raspberry Pi OS** (Debian Bookworm), am besten mit `sudo apt update && sudo apt full-upgrade`.
- **EEPROM** aktuell: `sudo rpi-eeprom-update` (ggf. neu starten und erneut prüfen).
- **PCIe** für NVMe ist am Pi 5 standardmäßig nutzbar; in neueren Bootloader-Versionen muss PCIe nicht mehr zwingend in `config.txt` stehen.

**NVMe hinter PCIe-Switch (z. B. Freenove Computer Case):** Boot von NVMe kann dort verzögert sein oder Retries auslösen. EEPROM aktuell halten; Details und Workarounds: **`docs/NVME_BOOT_FREENOVE_SWITCH.md`**.

---

## 3. Ablauf (Kurzfassung)

1. NVMe partitionieren: **Partition 1** = FAT32 (Boot, z. B. 256–512 MiB), **Partition 2** = ext4 (Rest = Root).
2. Inhalt von `/boot/firmware` (SD) nach NVMe Partition 1 kopieren.
3. Root-Dateisystem von der SD nach NVMe Partition 2 kopieren (rsync).
4. Auf der NVMe: **fstab** und **cmdline.txt** so anpassen, dass Root und Boot auf die NVMe-Partitionen zeigen.
5. In **config.txt** auf der NVMe-Boot-Partition ggf. PCIe aktivieren (siehe unten).
6. **Boot-Reihenfolge** im EEPROM auf NVMe setzen (z. B. `BOOT_ORDER=0xf146`).
7. Neustart; danach bootet der Pi von der NVMe. SD-Karte kann entfernt werden.

---

## 4. Manuelle Schritte (Detail)

### 4.1 NVMe partitionieren

**Hinweis:** Alle Daten auf der NVMe gehen verloren. Gerät z. B. `/dev/nvme0n1` (ohne Partitionsnummer).

```bash
# Gerät prüfen
lsblk
sudo fdisk -l /dev/nvme0n1

# Partitionierung (interaktiv oder per Script)
sudo fdisk /dev/nvme0n1
# In fdisk:
#   o     (neue DOS-Partitionstabelle)
#   n p 1 (Partition 1, primär)
#   Enter (Start default)
#   +256M (Größe für Boot, oder +512M)
#   t 1   (Typ)
#   c     (W95 FAT32 LBA)
#   n p 2 (Partition 2, primär)
#   Enter Enter (Rest der Platte)
#   w     (schreiben)
```

Boot-Partition formatieren und UUID setzen:

```bash
sudo mkfs.vfat -F 32 -n bootfs /dev/nvme0n1p1
sudo mkfs.ext4 -L rootfs /dev/nvme0n1p2
```

### 4.2 Boot-Partition (von SD) auf NVMe kopieren

```bash
sudo mkdir -p /mnt/nvme-boot /mnt/nvme-root
sudo mount /dev/nvme0n1p1 /mnt/nvme-boot
sudo mount /dev/nvme0n1p2 /mnt/nvme-root

# Inhalt von /boot/firmware (SD) nach NVMe p1
sudo rsync -a /boot/firmware/ /mnt/nvme-boot/
```

### 4.3 Root auf NVMe kopieren

```bash
# Wie beim PI-Installer-Klon: Root kopieren, Boot auslassen
sudo rsync -axHAWXS --numeric-ids \
  --exclude=/boot --exclude=/boot/firmware \
  --exclude=/proc --exclude=/sys --exclude=/dev --exclude=/tmp --exclude=/run \
  --exclude=/mnt --exclude=/lost+found --exclude=/mnt/nvme-boot --exclude=/mnt/nvme-root \
  / /mnt/nvme-root/
```

### 4.4 Konfiguration auf der NVMe anpassen

**cmdline.txt** (liegt jetzt auf `/mnt/nvme-boot/`):

- `root=` auf die Root-Partition der NVMe setzen, z. B. `root=/dev/nvme0n1p2`.

```bash
sudo sed -i 's|root=[^ ]*|root=/dev/nvme0n1p2|' /mnt/nvme-boot/cmdline.txt
```

**fstab** auf dem Root der NVMe (`/mnt/nvme-root/etc/fstab`):

- Zeile für `/` auf `/dev/nvme0n1p2` (ext4).
- Zeile für `/boot/firmware` auf `/dev/nvme0n1p1` (vfat).

Beispiel:

```
/dev/nvme0n1p2  /  ext4  defaults,noatime  0  1
/dev/nvme0n1p1  /boot/firmware  vfat  defaults,noatime  0  2
```

**config.txt** auf der NVMe-Boot-Partition (für Pi 5 PCIe, falls noch nicht vorhanden):

```
dtparam=pciex1
dtparam=pciex1_gen=3
```

### 4.5 Boot-Reihenfolge (EEPROM)

NVMe zuerst, dann z. B. USB, dann SD:

```bash
sudo -E rpi-eeprom-config --edit
```

In der geöffneten Datei z. B. setzen:

```
BOOT_ORDER=0xf146
```

- `6` = NVMe  
- `4` = USB-Massenspeicher  
- `1` = SD-Karte  
- `f` = von vorn beginnen

Speichern und schließen. Änderung wird beim nächsten Neustart aktiv.

```bash
sudo reboot
```

Nach dem Neustart sollte der Pi von der NVMe starten. Prüfen:

```bash
lsblk
findmnt /
# Root sollte /dev/nvme0n1p2 sein
```

---

## 5. Automatisches Skript (PI-Installer)

Im Projekt liegt ein Skript, das die Schritte 3.1–3.6 bündelt (Partitionierung, Kopieren, fstab/cmdline, EEPROM-Hinweis):

```bash
sudo ./scripts/setup-nvme-full-boot.sh
```

Voraussetzung: Sie starten **von der SD-Karte**; die NVMe ist angeschlossen und wird **komplett neu partitioniert** (alle Daten auf der NVMe gehen verloren). Das Skript fragt nach dem Ziellaufwerk (z. B. `/dev/nvme0n1`) und nach Bestätigung. Details und Sicherheitsabfragen siehe Skript und Abschnitt 7.

---

## 6. Speicher-Optimierung für den 8 GB Pi

Mit 8 GB RAM braucht das System weniger Swap; Sie können Speicher und Auslagerung anpassen.

| Thema | Empfehlung |
|-------|------------|
| **Swap** | `dphys-swapfile`: Bei 8 GB reicht eine kleine Swap-Datei (z. B. 1024 MB) oder Deaktivierung; siehe `PI_OPTIMIZATION.md`. |
| **zram** | Optional: `sudo apt install zram-tools` – komprimierter Swap im RAM, entlastet die NVMe. |
| **/tmp** | Oft bereits als tmpfs – in `fstab` prüfen (`tmpfs /tmp tmpfs …`). |
| **GPU-Speicher** | Unter „Raspberry Pi Config“ im PI-Installer oder in `config.txt`: z. B. 64–128 MB, um mehr RAM für das System zu lassen. |

Nach Umstellung auf NVMe-Vollboot liegen Swap und System auf der NVMe; bei 8 GB ist ein kleines Swap oder zram meist ausreichend.

---

## 7. Wichtige Hinweise

- **Backup:** Vor dem Umstellen ein Backup der SD-Karte oder des laufenden Systems anlegen (z. B. PI-Installer → Backup & Restore).
- **SD behalten:** Bis der erste Boot von der NVMe geklappt hat, die SD-Karte nicht löschen; bei Boot-Problemen können Sie sie wieder einstecken.
- **Boot-Reihenfolge:** Mit `BOOT_ORDER=0xf146` wird zuerst NVMe versucht; wenn die NVMe fehlt oder defekt ist, bootet der Pi von USB/SD (falls vorhanden).
- **Partitionen:** Verwenden Sie für Boot immer die **erste** Partition (FAT) und für Root die **zweite** (ext4), damit Bootloader und Kernel die erwartete Struktur finden.

---

## 8. NVMe prüfen (Diagnose)

Wenn der Pi **nicht von der NVMe startet** oder die NVMe **leer wirkt**:

1. **Mit SD-Karte booten** (falls Sie die SD entfernt hatten).
2. **Diagnose-Skript ausführen** (zeigt Erkennung, Partitionen, Inhalt von Boot/Root, EEPROM):
   ```bash
   sudo ./scripts/check-nvme-full-boot.sh
   ```
3. **Auswertung:**
   - **Keine NVMe gefunden:** PCIe-HAT/Kabel prüfen, `dmesg | grep -i nvme`.
   - **Keine Partitionen (p1/p2):** Partitionierung ist fehlgeschlagen oder die Platte wurde anders genutzt. Setup erneut ausführen: `sudo ./scripts/setup-nvme-full-boot.sh` (überschreibt die NVMe).
   - **Partitionen da, aber Boot/Root leer:** Kopiervorgang war abgebrochen oder fehlgeschlagen. Setup erneut ausführen.
   - **Boot-Partition ohne config.txt/cmdline.txt:** Setup erneut ausführen oder manuell von `/boot/firmware` nach NVMe p1 kopieren.
   - **BOOT_ORDER nicht 0xf146:** EEPROM anpassen: `sudo -E rpi-eeprom-config --edit` → `BOOT_ORDER=0xf146`.
   - **Alles OK (NVMe vollständig, BOOT_ORDER=0xf146), bootet aber weiter von SD:** siehe unten „NVMe vollständig, bootet trotzdem von SD“.

Nach erneutem Setup und gesetztem BOOT_ORDER Neustart: `sudo reboot`.

### 8.1 NVMe vollständig, bootet trotzdem von SD

Wenn die Diagnose zeigt: Partitionen OK, Boot- und Root-Inhalt OK, `BOOT_ORDER=0xf146` – Sie booten aber noch von `mmcblk0` (SD):

1. **SD-Karte physisch entfernen und neu starten**  
   Ohne SD muss der Bootloader von der NVMe starten (oder der Pi startet nicht). Wenn er dann von der NVMe bootet, war das Fallback auf die SD die Ursache. Danach können Sie die SD wieder einstecken (z. B. nur für Backup); beim nächsten Boot wird wieder zuerst NVMe versucht.

2. **PCIe auf der SD aktivieren**  
   Der Bootloader liest unter Umständen die Konfiguration von der zuerst erreichbaren Partition. Damit PCIe (für die NVMe) früh aktiv ist, auf der **SD-Karte** in `/boot/firmware/config.txt` eintragen:
   ```
   dtparam=pciex1
   dtparam=pciex1_gen=3
   ```
   Speichern, dann `sudo reboot`. Beim Neustart ist PCIe von vornherein aktiv; der Bootloader kann die NVMe zuverlässig ansprechen.

3. **EEPROM-Update prüfen**  
   `rpi-eeprom-config` (ohne `--edit`) ausführen und prüfen, ob `BOOT_ORDER=0xf146` in der angezeigten Konfiguration steht. Falls nicht: `sudo -E rpi-eeprom-config --edit`, eintragen, speichern und erneut neu starten.

### 8.2 NVMe-Boot schlägt fehl (Pi startet nicht von NVMe)

Wenn Sie **ohne SD** neu starten und der Pi **nicht** von der NVMe hochfährt (schwarzer Bildschirm, Timeout, oder Rückfall auf SD sobald SD drin ist):

1. **EEPROM auf neuesten Stand**  
   Der Bootloader muss NVMe unterstützen. Auf dem Pi (von SD gebootet):
   ```bash
   sudo rpi-eeprom-update
   ```
   Falls ein Update angeboten wird: anwenden, dann neu starten. Danach erneut NVMe-Boot ohne SD testen.

2. **Boot-Partition als bootbar markieren**  
   Manche Setups erwarten, dass die erste Partition das MBR-Boot-Flag hat. Von SD gebootet, NVMe p1 setzen:
   ```bash
   sudo sfdisk -A 1 /dev/nvme0n1
   ```
   (Partition 1 = bootable). Prüfen mit `sudo fdisk -l /dev/nvme0n1` (p1 sollte „Boot“ anzeigen).

3. **rootdelay in cmdline.txt auf der NVMe**  
   Der Kernel braucht manchmal etwas Zeit, bis die NVMe bereit ist. Auf der **NVMe-Boot-Partition** (z. B. nach `sudo mount /dev/nvme0n1p1 /mnt`) in `cmdline.txt` **rootdelay=10** ergänzen (einmalig, Leerzeichen davor):
   ```
   ... root=/dev/nvme0n1p2 rootdelay=10 ...
   ```
   Speichern, auswerfen, neu starten ohne SD.

4. **PCIe auf der SD aktivieren**  
   Damit der Bootloader PCIe beim nächsten Versuch (mit oder ohne SD) früh aktiviert, auf der **SD-Karte** in `/boot/firmware/config.txt` eintragen:
   ```
   dtparam=pciex1
   dtparam=pciex1_gen=3
   ```
   Speichern, SD drin lassen, neu starten. Beim nächsten Mal SD entfernen und erneut neu starten – der Bootloader hat PCIe dann ggf. zuverlässiger aktiv.

5. **Hinweis: NVMe nur mit USB-MSD**  
   In einigen Fällen (z. B. rpi-eeprom Issue #629) bootet der Pi von NVMe nur, wenn beim Start ein USB-Massenspeicher angeschlossen ist; danach kann er entfernt werden. Falls nichts anderes hilft, einmal mit angestecktem USB-Stick (ohne SD) testen.

---

## 9. Siehe auch

- `docs/PATHS_NVME.md` – Pfade und Hybrid-Boot (Boot auf SD, Root auf NVMe)
- `docs/CLONE_ARCHITECTURE.md` – Klon-Funktion im PI-Installer (nur Root auf NVMe)
- `PI_OPTIMIZATION.md` – Services und Swap-Optimierung auf dem Pi
- `docs/FREENOVE_COMPUTER_CASE.md` – Boot-Optionen (SD + NVMe / nur NVMe)
- `scripts/check-nvme-full-boot.sh` – NVMe-Diagnose (Partitionen, Boot-/Root-Inhalt, EEPROM)
