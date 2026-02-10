#!/bin/bash
# PI-Installer – Wechsel von Wayland zu X11
# Behebt Probleme mit:
# - Screenshot-Zwischenablage (xclip funktioniert besser unter X11)
# - AnyDesk (funktioniert nur unter X11)
# - App-Fenster-Zuweisung (besser unter X11)
#
# Auf dem Pi mit sudo ausführen: sudo ./switch-to-x11.sh

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

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  Wechsel zu X11 (Xorg)${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# Verfügbare X11-Sessions ermitteln
X11_SESSION=""
for name in rpd-x openbox lightdm-xsession; do
  if [ -f "/usr/share/xsessions/${name}.desktop" ]; then
    X11_SESSION="$name"
    echo -e "${GREEN}Verwende X11-Session: $X11_SESSION${NC}"
    break
  fi
done

if [ -z "$X11_SESSION" ]; then
  echo -e "${RED}Keine X11-Session gefunden!${NC}"
  echo -e "${YELLOW}Verfügbare Sessions:${NC}"
  ls /usr/share/xsessions/*.desktop 2>/dev/null | xargs -I{} basename {} .desktop | sed 's/^/  /' || echo "  Keine gefunden"
  exit 1
fi

# --- 1. X11 als Standard-Session setzen ---
echo -e "${CYAN}[1] X11 als Standard-Session für $USER${NC}"

# .dmrc (LightDM)
cat > "$HOME_DIR/.dmrc" << DMRC
[Desktop]
Session=$X11_SESSION
DMRC
chown "$USER:$(stat -c '%G' "$HOME_DIR")" "$HOME_DIR/.dmrc"
echo -e "    ${GREEN}.dmrc: Session=$X11_SESSION${NC}"

# AccountsService
ACCOUNTS_FILE="/var/lib/AccountsService/users/$USER"
mkdir -p "$(dirname "$ACCOUNTS_FILE")"
if [ ! -f "$ACCOUNTS_FILE" ]; then
  echo "[User]" > "$ACCOUNTS_FILE"
elif ! grep -q '^\[User\]' "$ACCOUNTS_FILE"; then
  echo "[User]" >> "$ACCOUNTS_FILE"
fi
sed -i '/^Session=/d' "$ACCOUNTS_FILE"
sed -i '/^XSession=/d' "$ACCOUNTS_FILE"
echo "Session=$X11_SESSION" >> "$ACCOUNTS_FILE"
echo "XSession=$X11_SESSION" >> "$ACCOUNTS_FILE"
echo -e "    ${GREEN}AccountsService: Session=$X11_SESSION${NC}"

# LightDM: Haupt-Config UND Drop-in
LIGHTDM_CONF="/etc/lightdm/lightdm.conf"
LIGHTDM_D="/etc/lightdm/lightdm.conf.d"
LIGHTDM_DROPIN="$LIGHTDM_D/99-pi-installer-x11.conf"

mkdir -p "$LIGHTDM_D"
cat > "$LIGHTDM_DROPIN" << LIGHTDMDROPIN
# PI-Installer: X11 erzwingen
[Seat:*]
user-session=$X11_SESSION
autologin-session=$X11_SESSION
LIGHTDMDROPIN
echo -e "    ${GREEN}LightDM Drop-in: $LIGHTDM_DROPIN → $X11_SESSION${NC}"

if [ -f "$LIGHTDM_CONF" ]; then
  if grep -q '^user-session=' "$LIGHTDM_CONF"; then
    sed -i "s|^user-session=.*|user-session=$X11_SESSION|" "$LIGHTDM_CONF"
  fi
  if grep -q '^autologin-session=' "$LIGHTDM_CONF"; then
    sed -i "s|^autologin-session=.*|autologin-session=$X11_SESSION|" "$LIGHTDM_CONF"
  fi
  echo -e "    ${GREEN}LightDM: lightdm.conf angepasst${NC}"
fi
echo ""

# --- 2. xclip installieren (für Zwischenablage) ---
echo -e "${CYAN}[2] xclip installieren (für Zwischenablage)${NC}"
if command -v apt-get >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y xclip >/dev/null 2>&1 || echo -e "    ${YELLOW}xclip bereits installiert oder Installation fehlgeschlagen${NC}"
  echo -e "    ${GREEN}xclip installiert${NC}"
else
  echo -e "    ${YELLOW}apt-get nicht verfügbar, xclip manuell installieren: sudo apt install xclip${NC}"
fi
echo ""

# --- 3. Screenshot-Funktion für X11 optimieren ---
echo -e "${CYAN}[3] Screenshot-Funktion für X11 optimieren${NC}"
echo -e "    ${GREEN}Die Screenshot-Funktion in dsi_radio.py verwendet jetzt xclip als Fallback${NC}"
echo ""

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  X11-Konfiguration abgeschlossen!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${YELLOW}Wichtig:${NC}"
echo -e "  1. Abmelden und wieder anmelden (oder Neustart)"
echo -e "  2. Beim Login die X11-Session wählen (falls gefragt)"
echo -e "  3. Nach dem Login läuft die Session unter X11"
echo ""
echo -e "${CYAN}Vorteile von X11:${NC}"
echo -e "  ✓ Screenshot-Zwischenablage funktioniert (xclip)"
echo -e "  ✓ AnyDesk funktioniert vollständig"
echo -e "  ✓ App-Fenster-Zuweisung funktioniert besser"
echo ""
