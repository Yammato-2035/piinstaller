#!/bin/bash
# PI-Installer – Wiederherstellung aus Backup
# Stellt die gesicherten Konfigurationsdateien wieder her
#
# Mit sudo ausführen: sudo ./restore-from-backup.sh BACKUP_DIR

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

USER="gabrielglienke"
HOME_DIR="/home/$USER"

if [ "$(id -u)" -ne 0 ]; then
  echo -e "${RED}Bitte mit sudo ausführen: sudo $0 BACKUP_DIR${NC}"
  exit 1
fi

if [ -z "$1" ]; then
  echo -e "${RED}Bitte Backup-Verzeichnis angeben!${NC}"
  echo -e "${YELLOW}Verfügbare Backups:${NC}"
  ls -d "$HOME_DIR"/system-backup-before-x11-* 2>/dev/null | sed 's/^/  /' || echo "  Keine Backups gefunden"
  exit 1
fi

BACKUP_DIR="$1"

if [ ! -d "$BACKUP_DIR" ]; then
  echo -e "${RED}Backup-Verzeichnis nicht gefunden: $BACKUP_DIR${NC}"
  exit 1
fi

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  Wiederherstellung aus Backup${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""
echo -e "${YELLOW}Backup-Verzeichnis: ${BACKUP_DIR}${NC}"
echo ""
read -p "Wirklich wiederherstellen? (j/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Jj]$ ]]; then
  echo -e "${YELLOW}Abgebrochen.${NC}"
  exit 0
fi

# --- 1. Session-Konfigurationen wiederherstellen ---
echo -e "${CYAN}[1] Session-Konfigurationen wiederherstellen${NC}"

# .dmrc
if [ -f "$BACKUP_DIR/.dmrc" ]; then
  cp "$BACKUP_DIR/.dmrc" "$HOME_DIR/.dmrc"
  chown "$USER:$(stat -c '%G' "$HOME_DIR")" "$HOME_DIR/.dmrc"
  echo -e "    ${GREEN}✓ .dmrc${NC}"
fi

# AccountsService
if [ -f "$BACKUP_DIR/AccountsService/users-$USER" ]; then
  ACCOUNTS_FILE="/var/lib/AccountsService/users/$USER"
  mkdir -p "$(dirname "$ACCOUNTS_FILE")"
  cp "$BACKUP_DIR/AccountsService/users-$USER" "$ACCOUNTS_FILE"
  echo -e "    ${GREEN}✓ AccountsService/users/$USER${NC}"
fi

# LightDM Config
if [ -f "$BACKUP_DIR/etc/lightdm/lightdm.conf" ]; then
  mkdir -p "/etc/lightdm"
  cp "$BACKUP_DIR/etc/lightdm/lightdm.conf" "/etc/lightdm/lightdm.conf"
  echo -e "    ${GREEN}✓ /etc/lightdm/lightdm.conf${NC}"
fi

# LightDM Drop-ins
if [ -d "$BACKUP_DIR/etc/lightdm/lightdm.conf.d" ]; then
  mkdir -p "/etc/lightdm/lightdm.conf.d"
  cp -r "$BACKUP_DIR/etc/lightdm/lightdm.conf.d"/* "/etc/lightdm/lightdm.conf.d/" 2>/dev/null || true
  echo -e "    ${GREEN}✓ /etc/lightdm/lightdm.conf.d/*${NC}"
fi

echo ""

# --- 2. Display-Konfigurationen wiederherstellen ---
echo -e "${CYAN}[2] Display-Konfigurationen wiederherstellen${NC}"

# Kanshi
if [ -d "$BACKUP_DIR/.config/kanshi" ]; then
  mkdir -p "$HOME_DIR/.config"
  rm -rf "$HOME_DIR/.config/kanshi" 2>/dev/null || true
  cp -r "$BACKUP_DIR/.config/kanshi" "$HOME_DIR/.config/kanshi"
  chown -R "$USER:$(stat -c '%G' "$HOME_DIR")" "$HOME_DIR/.config/kanshi"
  echo -e "    ${GREEN}✓ .config/kanshi${NC}"
fi

# Wayfire
if [ -f "$BACKUP_DIR/.config/wayfire.ini" ]; then
  mkdir -p "$HOME_DIR/.config"
  cp "$BACKUP_DIR/.config/wayfire.ini" "$HOME_DIR/.config/wayfire.ini"
  chown "$USER:$(stat -c '%G' "$HOME_DIR")" "$HOME_DIR/.config/wayfire.ini"
  echo -e "    ${GREEN}✓ .config/wayfire.ini${NC}"
fi

# Labwc
if [ -d "$BACKUP_DIR/.config/labwc" ]; then
  mkdir -p "$HOME_DIR/.config"
  rm -rf "$HOME_DIR/.config/labwc" 2>/dev/null || true
  cp -r "$BACKUP_DIR/.config/labwc" "$HOME_DIR/.config/labwc"
  chown -R "$USER:$(stat -c '%G' "$HOME_DIR")" "$HOME_DIR/.config/labwc"
  echo -e "    ${GREEN}✓ .config/labwc${NC}"
fi

# X11 Display-Konfigurationen
if [ -f "$BACKUP_DIR/.config/monitors.xml" ]; then
  mkdir -p "$HOME_DIR/.config"
  cp "$BACKUP_DIR/.config/monitors.xml" "$HOME_DIR/.config/monitors.xml"
  chown "$USER:$(stat -c '%G' "$HOME_DIR")" "$HOME_DIR/.config/monitors.xml"
  echo -e "    ${GREEN}✓ .config/monitors.xml${NC}"
fi

if [ -d "$BACKUP_DIR/.screenlayout" ]; then
  rm -rf "$HOME_DIR/.screenlayout" 2>/dev/null || true
  cp -r "$BACKUP_DIR/.screenlayout" "$HOME_DIR/.screenlayout"
  chown -R "$USER:$(stat -c '%G' "$HOME_DIR")" "$HOME_DIR/.screenlayout"
  echo -e "    ${GREEN}✓ .screenlayout${NC}"
fi

echo ""

# --- 3. Environment-Variablen wiederherstellen ---
echo -e "${CYAN}[3] Environment-Variablen wiederherstellen${NC}"

for file in .profile .bashrc .xprofile .xsessionrc .xinitrc; do
  if [ -f "$BACKUP_DIR/$file" ]; then
    cp "$BACKUP_DIR/$file" "$HOME_DIR/$file"
    chown "$USER:$(stat -c '%G' "$HOME_DIR")" "$HOME_DIR/$file"
    echo -e "    ${GREEN}✓ $file${NC}"
  fi
done

if [ -d "$BACKUP_DIR/.config/environment.d" ]; then
  mkdir -p "$HOME_DIR/.config"
  rm -rf "$HOME_DIR/.config/environment.d" 2>/dev/null || true
  cp -r "$BACKUP_DIR/.config/environment.d" "$HOME_DIR/.config/environment.d"
  chown -R "$USER:$(stat -c '%G' "$HOME_DIR")" "$HOME_DIR/.config/environment.d"
  echo -e "    ${GREEN}✓ .config/environment.d${NC}"
fi

echo ""

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Wiederherstellung abgeschlossen!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${YELLOW}Wichtig:${NC}"
echo -e "  Abmelden und wieder anmelden (oder Neustart), damit die Änderungen wirksam werden."
echo ""
