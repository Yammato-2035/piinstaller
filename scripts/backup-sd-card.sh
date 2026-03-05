#!/bin/bash
#
# backup-sd-card.sh – Sicherheits-Backup der SD-Karte (Boot + Root)
#
# Erstellt ein dateibasiertes Backup der aktuell genutzten Boot-Partition
# und des Root-Dateisystems. Ziel: z. B. NVMe oder USB (funktionierende SD
# sichern, bevor Boot von NVMe getestet wird).
#
# Mit sudo ausführen: sudo ./backup-sd-card.sh [ZIELVERZEICHNIS]
# Ohne Ziel: Nutzung eines Standardziels (siehe unten).
#
#   sudo ./backup-sd-card.sh --nvme   → Backup auf NVMe (ext4-Partition, vollständig)
#   sudo ./backup-sd-card.sh /pfad    → Backup ins angegebene Verzeichnis
#
# Optional: --image erzeugt zusätzlich ein Roh-Image der SD-Karte (dd).
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

DO_IMAGE=""
TARGET_DIR=""
USE_NVME=""

for arg in "$@"; do
  if [[ "$arg" == "--image" ]]; then
    DO_IMAGE=1
  elif [[ "$arg" == "--nvme" ]]; then
    USE_NVME=1
  elif [[ -z "$TARGET_DIR" && "$arg" != --* ]]; then
    TARGET_DIR="$arg"
  fi
done

if [[ $EUID -ne 0 ]]; then
  echo -e "${RED}Bitte mit sudo ausführen: sudo $0 [ZIELVERZEICHNIS] [--image]${NC}"
  exit 1
fi

# Boot- und Root-Partition ermitteln
BOOT_SOURCE=$(findmnt -n -o SOURCE /boot/firmware 2>/dev/null || true)
ROOT_SOURCE=$(findmnt -n -o SOURCE / 2>/dev/null || true)
if [[ -z "$BOOT_SOURCE" ]]; then
  BOOT_SOURCE=$(findmnt -n -o SOURCE /boot 2>/dev/null || true)
fi
if [[ -z "$BOOT_SOURCE" || -z "$ROOT_SOURCE" ]]; then
  echo -e "${RED}Konnte Boot oder Root-Mount nicht ermitteln.${NC}"
  exit 1
fi

# SD-Gerät (für optionales Image): Gerät von Boot-Partition (meist mmcblk0)
SD_DEVICE=""
if [[ "$BOOT_SOURCE" =~ ^/dev/(mmcblk[0-9]+) ]]; then
  SD_DEVICE="/dev/${BASH_REMATCH[1]}"
elif [[ "$BOOT_SOURCE" =~ ^/dev/([a-z]+[0-9]+) ]]; then
  SD_DEVICE="/dev/${BASH_REMATCH[1]}"
fi

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_NAME="sd-backup-$TIMESTAMP"

# Zielverzeichnis
if [[ -n "$USE_NVME" ]]; then
  # NVMe ext4-Partition finden (viel Platz, volle Backup-Qualität)
  ROOT_DEV=$(findmnt -n -o SOURCE / 2>/dev/null || true)
  NVME_EXT4=""
  while read -r name fstype; do
    [[ "$name" =~ ^nvme[0-9]+n[0-9]+p[0-9]+$ ]] || continue
    [[ "$fstype" == "ext4" ]] || continue
    dev="/dev/$name"
    [[ -b "$dev" ]] || continue
    [[ "$dev" == "$ROOT_DEV" ]] && continue
    NVME_EXT4="$dev"
    break
  done < <(lsblk -o NAME,FSTYPE -n -r 2>/dev/null)
  if [[ -z "$NVME_EXT4" ]]; then
    # Evtl. ist Root auf NVMe – dann größte andere ext4 nehmen oder dieselbe
    while read -r name fstype; do
      [[ "$name" =~ ^nvme[0-9]+n[0-9]+p[0-9]+$ ]] || continue
      [[ "$fstype" == "ext4" ]] || continue
      NVME_EXT4="/dev/$name"
      break
    done < <(lsblk -o NAME,FSTYPE -n -r 2>/dev/null)
  fi
  if [[ -z "$NVME_EXT4" || ! -b "$NVME_EXT4" ]]; then
    echo -e "${RED}Keine NVMe ext4-Partition gefunden. Bitte NVMe partitionieren (z. B. p2 ext4) oder Ziel angeben.${NC}"
    exit 1
  fi
  MOUNT_NVME="/mnt/nvme-backup"
  if ! mountpoint -q "$MOUNT_NVME" 2>/dev/null; then
    mkdir -p "$MOUNT_NVME"
    mount "$NVME_EXT4" "$MOUNT_NVME" || { echo -e "${RED}Mount von $NVME_EXT4 nach $MOUNT_NVME fehlgeschlagen.${NC}"; exit 1; }
  else
    # Prüfen, ob bereits unsere Partition gemountet ist
    CURRENT=$(findmnt -n -o SOURCE "$MOUNT_NVME" 2>/dev/null || true)
    if [[ "$CURRENT" != "$NVME_EXT4" ]]; then
      echo -e "${YELLOW}$MOUNT_NVME ist von $CURRENT gemountet. Nutze dieses Ziel.${NC}"
    fi
  fi
  BASE_DIR="$MOUNT_NVME/sd-backups"
  TARGET_DIR="$BASE_DIR"
elif [[ -n "$TARGET_DIR" ]]; then
  BASE_DIR="$TARGET_DIR"
else
  # Standard: erstes gemountetes NVMe- oder USB-Laufwerk mit Platz, sonst /root
  DEFAULT_ROOT="/root"
  shopt -s nullglob 2>/dev/null
  for mnt in /mnt/nvme* /mnt/nvme*/* /media/*/* /mnt/*; do
    [[ -d "$mnt" ]] || continue
    mountpoint -q "$mnt" 2>/dev/null || continue
    if df -B1 "$mnt" 2>/dev/null | awk 'NR==2 { exit ($4 > 2*1024*1024*1024) ? 0 : 1 }'; then
      DEFAULT_ROOT="$mnt"
      break
    fi
  done
  shopt -u nullglob 2>/dev/null
  BASE_DIR="${DEFAULT_ROOT}/sd-backups"
fi

BACKUP_DIR="$BASE_DIR/$BACKUP_NAME"
mkdir -p "$BACKUP_DIR"

# Dateisystem des Ziels: ext4/xfs/btrfs = volles Backup; vfat/exfat = eingeschränkt
TARGET_FSTYPE=$(findmnt -n -o FSTYPE -T "$BACKUP_DIR" 2>/dev/null || echo "vfat")
if [[ "$TARGET_FSTYPE" == "ext4" || "$TARGET_FSTYPE" == "ext3" || "$TARGET_FSTYPE" == "btrfs" || "$TARGET_FSTYPE" == "xfs" ]]; then
  RSYNC_SAFE_EXTRAS=""   # Symlinks, Besitzer, Sockets erlaubt
else
  RSYNC_SAFE_EXTRAS="--no-owner --no-group --copy-links --no-devices --no-specials"
fi

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  SD-Karten-Backup${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""
echo -e "  Boot:  $BOOT_SOURCE"
echo -e "  Root:  $ROOT_SOURCE"
echo -e "  Ziel:  $BACKUP_DIR"
[[ -n "$USE_NVME" ]] && echo -e "  ${GREEN}→ Vollständiges Backup auf NVMe (ext4), unabhängig von der SD-Karte.${NC}"
[[ -n "$RSYNC_SAFE_EXTRAS" ]] && echo -e "  ${YELLOW}→ Ziel ist vfat/exfat – Backup eingeschränkt (Symlinks/Besitzer angepasst).${NC}"
echo ""

# 1. Boot-Partition sichern
echo -e "${CYAN}[1] Sichere /boot/firmware …${NC}"
mkdir -p "$BACKUP_DIR/boot_firmware"
if [[ -n "$RSYNC_SAFE_EXTRAS" ]]; then
  rsync -a --delete $RSYNC_SAFE_EXTRAS /boot/firmware/ "$BACKUP_DIR/boot_firmware/" 2>/dev/null || \
    rsync -a --delete $RSYNC_SAFE_EXTRAS /boot/ "$BACKUP_DIR/boot_firmware/" 2>/dev/null || true
else
  rsync -a --delete /boot/firmware/ "$BACKUP_DIR/boot_firmware/" 2>/dev/null || \
    rsync -a --delete /boot/ "$BACKUP_DIR/boot_firmware/" 2>/dev/null || true
fi
echo -e "    ${GREEN}✓ boot_firmware/${NC}"

# 2. Root-Dateisystem sichern (ohne Boot, /proc, /sys, etc.)
# Auf ext4: volle Treue (Symlinks, Besitzer). Auf vfat: eingeschränkt.
echo -e "${CYAN}[2] Sichere Root-Dateisystem (rsync) …${NC}"
mkdir -p "$BACKUP_DIR/root"
rsync -axHAWXS --numeric-ids $RSYNC_SAFE_EXTRAS \
  --exclude=/boot \
  --exclude=/boot/firmware \
  --exclude=/proc \
  --exclude=/sys \
  --exclude=/dev \
  --exclude=/tmp \
  --exclude=/run \
  --exclude=/mnt \
  --exclude=/lost+found \
  --exclude="$BACKUP_DIR" \
  / "$BACKUP_DIR/root/"
echo -e "    ${GREEN}✓ root/${NC}"

# 3. Manifest für Wiederherstellung
MANIFEST="$BACKUP_DIR/MANIFEST.txt"
{
  echo "SD-Karten-Backup – $TIMESTAMP"
  echo "Erstellt: $(date -Iseconds)"
  echo ""
  echo "Quell-Boot:  $BOOT_SOURCE"
  echo "Quell-Root:  $ROOT_SOURCE"
  echo "SD-Gerät:    ${SD_DEVICE:-unbekannt}"
  echo ""
  echo "Partitionen (lsblk):"
  lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT "$ROOT_SOURCE" 2>/dev/null || true
  echo ""
  echo "Wiederherstellung (Kurz):"
  echo "  - Neue SD partitionieren (p1 FAT32 Boot, p2 ext4 Root), mounten."
  echo "  - rsync -a $BACKUP_DIR/boot_firmware/ /mnt/boot/"
  echo "  - rsync -axHAWXS ... $BACKUP_DIR/root/ /mnt/root/"
  echo "  - cmdline.txt/fstab anpassen (root=..., Boot-Partition)."
  echo "  Siehe auch: docs/NVME_FULL_BOOT.md, scripts/setup-nvme-full-boot.sh"
} > "$MANIFEST"
echo -e "${CYAN}[3] Manifest: $MANIFEST${NC}"

# 4. Optional: Roh-Image der SD-Karte
if [[ -n "$DO_IMAGE" && -n "$SD_DEVICE" && -b "$SD_DEVICE" ]]; then
  IMAGE_FILE="$BACKUP_DIR/sd-card.img"
  echo -e "${CYAN}[4] Erstelle Roh-Image: $IMAGE_FILE (kann lange dauern) …${NC}"
  dd if="$SD_DEVICE" of="$IMAGE_FILE" bs=4M status=progress conv=fsync 2>/dev/null || \
    dd if="$SD_DEVICE" of="$IMAGE_FILE" bs=4M conv=fsync
  echo -e "    ${GREEN}✓ sd-card.img${NC}"
  echo "    Wiederherstellung Image: dd if=$IMAGE_FILE of=SD_DEVICE bs=4M status=progress conv=fsync"
else
  if [[ -n "$DO_IMAGE" && -z "$SD_DEVICE" ]]; then
    echo -e "${YELLOW}[4] --image angegeben, aber SD-Gerät nicht ermittelt (Boot nicht von SD?). Image übersprungen.${NC}"
  fi
fi

echo ""
echo -e "${GREEN}Backup abgeschlossen: $BACKUP_DIR${NC}"
echo ""
echo "Nächste Schritte:"
echo "  - Backup z. B. auf PC kopieren oder auf NVMe belassen."
echo "  - Bei Bedarf Wiederherstellung aus boot_firmware/ und root/ (siehe MANIFEST.txt)."
echo ""
