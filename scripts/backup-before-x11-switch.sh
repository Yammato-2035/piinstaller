#!/bin/bash
# PI-Installer – Backup vor X11-Wechsel
# Sichert alle relevanten Konfigurationsdateien vor dem Wechsel von Wayland zu X11
#
# Mit sudo ausführen: sudo ./backup-before-x11-switch.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

USER="gabrielglienke"
HOME_DIR="/home/$USER"

if [ "$(id -u)" -ne 0 ]; then
  echo -e "${RED}Bitte mit sudo ausführen: sudo $0${NC}"
  exit 1
fi

if [ ! -d "$HOME_DIR" ]; then
  echo -e "${RED}Benutzer $USER nicht gefunden ($HOME_DIR)${NC}"
  exit 1
fi

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="$HOME_DIR/system-backup-before-x11-$TIMESTAMP"

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  System-Backup vor X11-Wechsel${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""
echo -e "${CYAN}Backup-Verzeichnis: ${BACKUP_DIR}${NC}"
echo ""

mkdir -p "$BACKUP_DIR"
chown "$USER:$(stat -c '%G' "$HOME_DIR")" "$BACKUP_DIR"

# --- 1. Session-Konfigurationen ---
echo -e "${CYAN}[1] Session-Konfigurationen sichern${NC}"

# .dmrc
if [ -f "$HOME_DIR/.dmrc" ]; then
  cp "$HOME_DIR/.dmrc" "$BACKUP_DIR/.dmrc"
  echo -e "    ${GREEN}✓ .dmrc${NC}"
fi

# AccountsService
ACCOUNTS_FILE="/var/lib/AccountsService/users/$USER"
if [ -f "$ACCOUNTS_FILE" ]; then
  mkdir -p "$BACKUP_DIR/AccountsService"
  cp "$ACCOUNTS_FILE" "$BACKUP_DIR/AccountsService/users-$USER"
  echo -e "    ${GREEN}✓ AccountsService/users/$USER${NC}"
fi

# LightDM Config
LIGHTDM_CONF="/etc/lightdm/lightdm.conf"
if [ -f "$LIGHTDM_CONF" ]; then
  mkdir -p "$BACKUP_DIR/etc/lightdm"
  cp "$LIGHTDM_CONF" "$BACKUP_DIR/etc/lightdm/lightdm.conf"
  echo -e "    ${GREEN}✓ /etc/lightdm/lightdm.conf${NC}"
fi

# LightDM Drop-ins
LIGHTDM_D="/etc/lightdm/lightdm.conf.d"
if [ -d "$LIGHTDM_D" ]; then
  mkdir -p "$BACKUP_DIR/etc/lightdm/lightdm.conf.d"
  cp -r "$LIGHTDM_D"/* "$BACKUP_DIR/etc/lightdm/lightdm.conf.d/" 2>/dev/null || true
  echo -e "    ${GREEN}✓ /etc/lightdm/lightdm.conf.d/*${NC}"
fi

echo ""

# --- 2. Display-Konfigurationen ---
echo -e "${CYAN}[2] Display-Konfigurationen sichern${NC}"

# Kanshi (Wayland Display-Manager)
if [ -d "$HOME_DIR/.config/kanshi" ]; then
  mkdir -p "$BACKUP_DIR/.config"
  cp -r "$HOME_DIR/.config/kanshi" "$BACKUP_DIR/.config/kanshi"
  echo -e "    ${GREEN}✓ .config/kanshi${NC}"
fi

# Wayfire config
if [ -f "$HOME_DIR/.config/wayfire.ini" ]; then
  mkdir -p "$BACKUP_DIR/.config"
  cp "$HOME_DIR/.config/wayfire.ini" "$BACKUP_DIR/.config/wayfire.ini"
  echo -e "    ${GREEN}✓ .config/wayfire.ini${NC}"
fi

# Labwc config
if [ -d "$HOME_DIR/.config/labwc" ]; then
  mkdir -p "$BACKUP_DIR/.config"
  cp -r "$HOME_DIR/.config/labwc" "$BACKUP_DIR/.config/labwc"
  echo -e "    ${GREEN}✓ .config/labwc${NC}"
fi

# X11 Display-Konfigurationen
if [ -f "$HOME_DIR/.config/monitors.xml" ]; then
  mkdir -p "$BACKUP_DIR/.config"
  cp "$HOME_DIR/.config/monitors.xml" "$BACKUP_DIR/.config/monitors.xml"
  echo -e "    ${GREEN}✓ .config/monitors.xml${NC}"
fi

if [ -d "$HOME_DIR/.screenlayout" ]; then
  mkdir -p "$BACKUP_DIR"
  cp -r "$HOME_DIR/.screenlayout" "$BACKUP_DIR/.screenlayout"
  echo -e "    ${GREEN}✓ .screenlayout${NC}"
fi

echo ""

# --- 3. Environment-Variablen ---
echo -e "${CYAN}[3] Environment-Variablen sichern${NC}"

# .profile, .bashrc, .xprofile, etc.
for file in .profile .bashrc .xprofile .xsessionrc .xinitrc; do
  if [ -f "$HOME_DIR/$file" ]; then
    cp "$HOME_DIR/$file" "$BACKUP_DIR/$file"
    echo -e "    ${GREEN}✓ $file${NC}"
  fi
done

# .config/environment.d (systemd user environment)
if [ -d "$HOME_DIR/.config/environment.d" ]; then
  mkdir -p "$BACKUP_DIR/.config"
  cp -r "$HOME_DIR/.config/environment.d" "$BACKUP_DIR/.config/environment.d"
  echo -e "    ${GREEN}✓ .config/environment.d${NC}"
fi

echo ""

# --- 4. Aktuelle Session-Info ---
echo -e "${CYAN}[4] Aktuelle System-Info sichern${NC}"

{
  echo "=== System Info ==="
  echo "Timestamp: $(date)"
  echo "User: $USER"
  echo "Session Type: ${XDG_SESSION_TYPE:-unknown}"
  echo "Display: ${DISPLAY:-not set}"
  echo "Wayland Display: ${WAYLAND_DISPLAY:-not set}"
  echo ""
  echo "=== Aktuelle Session ==="
  loginctl show-session $(loginctl | grep "$USER" | head -1 | awk '{print $1}') 2>/dev/null || echo "Session-Info nicht verfügbar"
  echo ""
  echo "=== Verfügbare Sessions ==="
  echo "X11 Sessions:"
  ls /usr/share/xsessions/*.desktop 2>/dev/null | xargs -I{} basename {} .desktop | sed 's/^/  /' || echo "  Keine gefunden"
  echo ""
  echo "Wayland Sessions:"
  ls /usr/share/wayland-sessions/*.desktop 2>/dev/null | xargs -I{} basename {} .desktop | sed 's/^/  /' || echo "  Keine gefunden"
} > "$BACKUP_DIR/system-info.txt"
chown "$USER:$(stat -c '%G' "$HOME_DIR")" "$BACKUP_DIR/system-info.txt"
echo -e "    ${GREEN}✓ system-info.txt${NC}"

echo ""

# --- 5. Installierte Pakete (für xclip, etc.) ---
echo -e "${CYAN}[5] Paket-Liste sichern${NC}"
dpkg -l | grep -E "(xclip|wl-clipboard|lightdm|wayland|xorg)" > "$BACKUP_DIR/installed-packages.txt" 2>/dev/null || true
chown "$USER:$(stat -c '%G' "$HOME_DIR")" "$BACKUP_DIR/installed-packages.txt"
echo -e "    ${GREEN}✓ installed-packages.txt${NC}"

echo ""

# --- Zusammenfassung ---
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Backup abgeschlossen!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${CYAN}Backup-Verzeichnis:${NC}"
echo -e "  ${BACKUP_DIR}${NC}"
echo ""
echo -e "${YELLOW}Inhalt:${NC}"
ls -lh "$BACKUP_DIR" | tail -n +2 | sed 's/^/  /'
echo ""
echo -e "${CYAN}Nächste Schritte:${NC}"
echo -e "  1. Backup prüfen: ls -la ${BACKUP_DIR}${NC}"
echo -e "  2. X11-Wechsel durchführen: sudo ./switch-to-x11.sh${NC}"
echo -e "  3. Falls Probleme: Backup wiederherstellen mit restore-from-backup.sh${NC}"
echo ""
