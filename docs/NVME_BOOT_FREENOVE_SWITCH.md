# NVMe-Boot mit Freenove-Computer-Case (PCIe-Switch)

**Erstellt:** 2026-02-28  
**Zweck:** Boot von NVMe, wenn die SSD **hinter dem PCIe-Switch** (ASM1184e) im Freenove-Gehäuse hängt – und was tun, wenn der Bootloader die NVMe beim Start (noch) nicht findet.

---

## 1. Ausgangslage

- **NVMe wird unter Linux erkannt** (`/dev/nvme*`, `nvme list`).
- **Boot von NVMe** gelingt bisher nicht: Vermutung „Switch zu langsam“, NVMe beim Boot noch nicht sichtbar.
- **Freenove Computer Case:** NVMe steckt hinter einem **ASMedia ASM1184e** PCIe-Switch (4-Port). Der Pi-5-Bootloader muss den PCIe-Baum durchlaufen, um die NVMe zu finden.

---

## 2. Was hilft: EEPROM aktuell halten

Seit **Bootloader-Release 2024-06-05** unterstützt der Raspberry-Pi-5-Bootloader das **Enumerieren von NVMe hinter PCIe-Switches** (u. a. ASM1182e/ASM1184e). Vorher schlug Boot mit „Failed to open device: 'nvme'“ fehl.

**Schritte:**

```bash
sudo rpi-eeprom-update
# Falls Update angeboten wird: anwenden, dann Neustart
sudo reboot
# Nach dem Neustart erneut prüfen
sudo rpi-eeprom-update
```

- **Firmware-Status:** Siehe [raspberrypi/firmware#1833](https://github.com/raspberrypi/firmware/issues/1833) (Closed: Boot von NVMe hinter Switch wurde umgesetzt).

---

## 3. Boot-Reihenfolge (BOOT_ORDER)

Damit der Pi überhaupt von NVMe versucht zu starten:

```bash
sudo -E rpi-eeprom-config --edit
```

Eintrag setzen/anpassen:

- **BOOT_ORDER=0xf146**  
  Bedeutung: Reihenfolge **6** (NVMe) → **4** (USB) → **1** (SD). Das **f** bedeutet „von vorn durchprobieren“.

Nach Speichern und Neustart versucht der Bootloader zuerst NVMe, dann USB, dann SD.

---

## 4. Boot mit „Pause“ / Debug: UART (Serial)

Es gibt **keine EEPROM-Option für eine manuelle Pause** vor dem Boot. Was du tun kannst:

- **UART aktivieren**, Bootloader-Ausgabe am Serial-Adapter (3,3 V!) mitlesen. Dann siehst du:
  - ob „Failed to open device: 'nvme'“ kommt,
  - ob „Retry NVME 1“ mehrfach erscheint (Bootloader macht von sich aus Retries, das kann 10+ Sekunden dauern).

**UART im EEPROM:**

```bash
sudo rpi-eeprom-config --edit
# Eintrag: BOOT_UART=1
```

Danach Neustart; Serial an **GPIO 14 (Tx) / 15 (Rx)** und GND (3,3 V Level, z. B. USB-UART-Adapter). Mit Putty/minicom/screen (115200 8N1) siehst du die Bootloader-Meldungen. So kannst du prüfen, ob der Bootloader die NVMe hinter dem Switch überhaupt sieht oder ob es bei Retries bleibt.

---

## 5. Wenn Boot von NVMe weiter scheitert: Workarounds

| Variante | Beschreibung |
|----------|--------------|
| **Hybrid (aktuell)** | Boot von **SD**, Root auf **NVMe**. Läuft bei euch bereits; Einstellungen liegen auf der reparierten SD (+ Root auf NVMe). |
| **SD-Backup** | Funktionierende SD **sichern** (Boot + Root), bevor ihr Boot-Reihenfolge oder NVMe-Vollboot testet: `sudo ./scripts/backup-sd-card.sh [Ziel z. B. /mnt/…]` – siehe unten. |
| **Vollboot NVMe später** | Wenn EEPROM und ggf. zukünftige Bootloader-Updates den Switch zuverlässig unterstützen: System mit `scripts/setup-nvme-full-boot.sh` auf NVMe kopieren und BOOT_ORDER=0xf146 setzen. |

**Hinweis:** Einige Nutzer berichten von **deutlich längeren Boot-Zeiten** (10–90 s), bis der Bootloader NVMe hinter dem Switch findet. Wenn UART „Retry NVME“ zeigt, einfach **länger warten** (z. B. 30–60 s), bevor abgebrochen wird.

---

## 6. SD-Karte sichern (Sicherheit vor Tests)

Bevor ihr BOOT_ORDER auf NVMe umstellt oder an der Boot-SD experimentiert:

```bash
# Backup auf NVMe (z. B. bestehende Partition mounten)
sudo mkdir -p /mnt/backup
sudo mount /dev/nvme0n1p1 /mnt/backup   # oder eine andere Partition
sudo ./scripts/backup-sd-card.sh /mnt/backup

# Optional: zusätzlich Roh-Image der SD (lange Laufzeit, viel Platz)
sudo ./scripts/backup-sd-card.sh /mnt/backup --image
```

Das Skript sichert **Boot-Partition** und **Root** dateibasiert; mit `--image` zusätzlich ein Roh-Image der SD. Wiederherstellungshinweise stehen in `MANIFEST.txt` im Backup-Ordner.

---

## 7. Kurzfassung

1. **EEPROM updaten:** `sudo rpi-eeprom-update` → ggf. Neustart.  
2. **BOOT_ORDER=0xf146** setzen, wenn von NVMe gebootet werden soll.  
3. **UART (BOOT_UART=1)** nutzen, um Boot-Verlauf zu sehen und ggf. **länger warten** (Retries).  
4. **SD-Backup** vor Änderungen an Boot-Reihenfolge oder Boot-Partition anlegen: `scripts/backup-sd-card.sh`.

Siehe auch: `docs/NVME_FULL_BOOT.md`, `docs/PATHS_NVME.md`.
