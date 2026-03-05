#!/bin/bash
#
# setup-nvme-full-boot.sh
# Richtet die angeschlossene NVMe so ein, dass der Raspberry Pi 5
# vollständig von der NVMe startet (Boot + Root). Die SD-Karte wird
# auf die NVMe überspielt; danach kann die SD-Karte entfernt werden.
#
# Voraussetzung: Pi 5, Boot von SD, NVMe angeschlossen (z. B. M.2 HAT+).
# ACHTUNG: Alle Daten auf der NVMe werden gelöscht.
#
# Siehe: docs/NVME_FULL_BOOT.md
#

set -e
BOOT_SIZE_MB=256
MOUNT_BOOT="/mnt/nvme-full-boot"
MOUNT_ROOT="/mnt/nvme-full-root"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
err() { echo "FEHLER: $*" >&2; exit 1; }

# Root-Rechte
if [[ $EUID -ne 0 ]]; then
  echo "Bitte mit sudo ausführen: sudo $0"
  exit 1
fi

# Raspberry Pi 5?
if [[ ! -f /proc/device-tree/model ]]; then
  err "Kein Raspberry Pi erkannt (/proc/device-tree/model)."
fi
MODEL=$(tr -d '\0' < /proc/device-tree/model 2>/dev/null || true)
if [[ "$MODEL" != *"Raspberry Pi 5"* ]]; then
  err "Dieses Skript ist für den Raspberry Pi 5 gedacht. Erkannt: $MODEL"
fi

# NVMe-Geräte (ohne Partitionsnummer)
NVME_BLOCKS=()
while read -r line; do
  if [[ "$line" =~ ^/dev/(nvme[0-9]+n[0-9]+)$ ]]; then
    NVME_BLOCKS+=("${BASH_REMATCH[1]}")
  fi
done < <(lsblk -d -n -o NAME,TRAN 2>/dev/null | awk '$2=="nvme" {print "/dev/"$1}')

if [[ ${#NVME_BLOCKS[@]} -eq 0 ]]; then
  err "Keine NVMe-Blockgeräte gefunden. Bitte NVMe anschließen (z. B. M.2 HAT+)."
fi

# Auswahl
NVME_DEV=""
if [[ ${#NVME_BLOCKS[@]} -eq 1 ]]; then
  NVME_DEV="/dev/${NVME_BLOCKS[0]}"
  log "NVMe gefunden: $NVME_DEV"
else
  echo "Mehrere NVMe-Geräte gefunden:"
  for i in "${!NVME_BLOCKS[@]}"; do
    echo "  $((i+1))) /dev/${NVME_BLOCKS[$i]}"
  done
  read -rp "Nummer wählen (1-${#NVME_BLOCKS[@]}): " num
  if [[ "$num" =~ ^[0-9]+$ ]] && (( num >= 1 && num <= ${#NVME_BLOCKS[@]} )); then
    NVME_DEV="/dev/${NVME_BLOCKS[$((num-1))]}"
  else
    err "Ungültige Auswahl."
  fi
fi

# Sicherheitsabfrage
echo ""
echo "=== ACHTUNG ==="
echo "Auf $NVME_DEV werden ALLE Daten gelöscht."
echo "Es werden zwei Partitionen angelegt:"
echo "  - Partition 1: ${BOOT_SIZE_MB} MiB FAT32 (Boot)"
echo "  - Partition 2: Rest ext4 (Root)"
echo "Anschließend wird das aktuelle System (SD) auf die NVMe kopiert"
echo "und die Boot-Reihenfolge kann auf NVMe umgestellt werden."
echo ""
read -rp "Fortfahren? (ja eingeben): " confirm
if [[ "$confirm" != "ja" ]]; then
  echo "Abgebrochen."
  exit 0
fi

# Partitionsnummern
NVME_BASE="${NVME_DEV#/dev/}"
P1="${NVME_DEV}p1"
P2="${NVME_DEV}p2"

# Eventuell gemountete Partitionen aushängen
for m in "$P1" "$P2"; do
  mountpoint -q "$m" 2>/dev/null && umount "$m"
done
for m in "$MOUNT_BOOT" "$MOUNT_ROOT"; do
  mountpoint -q "$m" 2>/dev/null && umount "$m"
done

# Partitionstabelle anlegen: 1 = FAT32 (Boot), 2 = ext4 (Root)
# Komma-Format (start, size, type) funktioniert mit älterem und neuem sfdisk.
# 256 MiB = 524288 Sektoren à 512 Byte.
log "Partitionierung von $NVME_DEV …"
sfdisk --delete "$NVME_DEV" 2>/dev/null || true
BOOT_SECTORS=$((BOOT_SIZE_MB * 2048))
if ! printf "2048,%d,c\n,,83\n" "$BOOT_SECTORS" | sfdisk "$NVME_DEV"; then
  err "Partitionierung fehlgeschlagen. Bitte manuell: fdisk $NVME_DEV → p1 256M Typ c (FAT32), p2 Rest Typ 83 (ext4)."
fi

# Partitionsknoten anlegen (udev)
sleep 2
partprobe "$NVME_DEV" 2>/dev/null || true
sleep 1
if ! [[ -b "$P1" ]] || ! [[ -b "$P2" ]]; then
  err "Partitionen $P1 / $P2 nicht gefunden. Bitte: lsblk $NVME_DEV und ggf. Neustart oder manuell partitionieren."
fi

# Partition 1 als bootbar markieren (MBR Boot-Flag; manche Bootloader erwarten das)
sfdisk -A 1 "$NVME_DEV" 2>/dev/null || true

# Dateisysteme anlegen
log "Formatiere $P1 (FAT32) …"
mkfs.vfat -F 32 -n bootfs "$P1"
log "Formatiere $P2 (ext4) …"
mkfs.ext4 -L rootfs "$P2"

# Mount-Punkte
mkdir -p "$MOUNT_BOOT" "$MOUNT_ROOT"
mount "$P1" "$MOUNT_BOOT"
mount "$P2" "$MOUNT_ROOT"

# Boot von SD nach NVMe p1 kopieren
log "Kopiere Boot-Partition (/boot/firmware) nach $P1 …"
if [[ -d /boot/firmware ]]; then
  rsync -a /boot/firmware/ "$MOUNT_BOOT/"
else
  rsync -a /boot/ "$MOUNT_BOOT/" 2>/dev/null || true
fi

# Root nach NVMe p2 kopieren (wie PI-Installer-Klon)
log "Kopiere Root-Dateisystem nach $P2 (kann mehrere Minuten dauern) …"
rsync -axHAWXS --numeric-ids \
  --exclude=/boot \
  --exclude=/boot/firmware \
  --exclude=/proc \
  --exclude=/sys \
  --exclude=/dev \
  --exclude=/tmp \
  --exclude=/run \
  --exclude=/mnt \
  --exclude=/lost+found \
  --exclude="$MOUNT_BOOT" \
  --exclude="$MOUNT_ROOT" \
  / "$MOUNT_ROOT/"

# cmdline.txt auf der NVMe-Boot-Partition: root= auf p2 setzen, rootdelay=10 für NVMe-Init
CMDLINE="$MOUNT_BOOT/cmdline.txt"
if [[ -f "$CMDLINE" ]]; then
  sed -i "s|root=[^ ]*|root=$P2|" "$CMDLINE"
  if ! grep -q 'rootdelay=' "$CMDLINE"; then
    sed -i "s|root=$P2|root=$P2 rootdelay=10|" "$CMDLINE"
    log "cmdline.txt: rootdelay=10 ergänzt"
  fi
  log "cmdline.txt angepasst: root=$P2"
fi

# config.txt: PCIe für Pi 5 (falls noch nicht vorhanden)
CONFIG="$MOUNT_BOOT/config.txt"
if [[ -f "$CONFIG" ]]; then
  if ! grep -q "dtparam=pciex1" "$CONFIG"; then
    echo "" >> "$CONFIG"
    echo "# NVMe PCIe (Pi 5)" >> "$CONFIG"
    echo "dtparam=pciex1" >> "$CONFIG"
    echo "dtparam=pciex1_gen=3" >> "$CONFIG"
    log "config.txt: PCIe-Parameter ergänzt."
  fi
fi

# fstab auf dem Root der NVMe: Root + Boot
FSTAB="$MOUNT_ROOT/etc/fstab"
if [[ -f "$FSTAB" ]]; then
  # Root-Zeile ersetzen und Boot-Zeile sicherstellen
  TMP=$(mktemp)
  ROOT_SET=0
  BOOT_SET=0
  while IFS= read -r line; do
    if [[ "$line" =~ ^[[:space:]]*# ]]; then
      echo "$line" >> "$TMP"
      continue
    fi
    parts=($line)
    if [[ ${#parts[@]} -ge 2 && "${parts[1]}" == "/" ]]; then
      echo "$P2  /  ext4  defaults,noatime  0  1" >> "$TMP"
      ROOT_SET=1
    elif [[ ${#parts[@]} -ge 2 && "${parts[1]}" == "/boot/firmware" ]]; then
      echo "$P1  /boot/firmware  vfat  defaults,noatime  0  2" >> "$TMP"
      BOOT_SET=1
    else
      echo "$line" >> "$TMP"
    fi
  done < "$FSTAB"
  if [[ $ROOT_SET -eq 0 ]]; then
    echo "$P2  /  ext4  defaults,noatime  0  1" >> "$TMP"
  fi
  if [[ $BOOT_SET -eq 0 ]]; then
    echo "$P1  /boot/firmware  vfat  defaults,noatime  0  2" >> "$TMP"
  fi
  cat "$TMP" > "$FSTAB"
  rm -f "$TMP"
  log "fstab angepasst."
fi

# Aushängen
umount "$MOUNT_BOOT"
umount "$MOUNT_ROOT"
rmdir "$MOUNT_BOOT" "$MOUNT_ROOT" 2>/dev/null || true

log "Kopieren und Konfiguration abgeschlossen."
echo ""
echo "=== Nächste Schritte ==="
echo "1. Boot-Reihenfolge auf NVMe setzen:"
echo "   sudo -E rpi-eeprom-config --edit"
echo "   In der Datei eintragen bzw. anpassen: BOOT_ORDER=0xf146"
echo "   (6=NVMe, 4=USB, 1=SD; f=von vorn)"
echo ""
echo "2. Neustart: sudo reboot"
echo ""
echo "3. Nach dem Neustart sollte der Pi von der NVMe starten."
echo "   Prüfen mit: lsblk und findmnt /"
echo ""
echo "Ausführliche Anleitung: docs/NVME_FULL_BOOT.md"
