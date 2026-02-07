#!/bin/bash
# PI-Installer – gabrielglienke: Wayland + Dual Display (DSI+HDMI)
# 1. Setzt Wayland als Standard-Session für gabrielglienke
# 2. Entfernt/backt Display-Configs, die HDMI beim Login ausschalten
# 3. Erstellt wayfire.ini mit Dual Display
#
# Auf dem Pi mit sudo ausführen: sudo ./fix-gabriel-dual-display-wayland.sh

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
echo -e "${CYAN}  gabrielglienke: Wayland + Dual Display${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# --- 1. Wayland als Standard-Session setzen ---
echo -e "${CYAN}[1] Wayland als Standard-Session für $USER${NC}"

# Verfügbare Wayland-Sessions ermitteln (Pi OS: labwc, rpd-labwc, pix-wayfire)
WAYLAND_SESSION=""
for name in rpd-labwc labwc pix-wayfire wayfire LXDE-pi-wayfire pix; do
  if [ -f "/usr/share/wayland-sessions/${name}.desktop" ]; then
    WAYLAND_SESSION="$name"
    break
  fi
done

# Prüfen ob Session existiert und Wayland erzwingen
if [ -n "$WAYLAND_SESSION" ]; then
  # .dmrc (LightDM)
  cat > "$HOME_DIR/.dmrc" << DMRC
[Desktop]
Session=$WAYLAND_SESSION
DMRC
  chown "$USER:$(stat -c '%G' "$HOME_DIR")" "$HOME_DIR/.dmrc"
  echo -e "    ${GREEN}.dmrc: Session=$WAYLAND_SESSION${NC}"

  # AccountsService (überschreibt X11-Preferenz)
  ACCOUNTS_FILE="/var/lib/AccountsService/users/$USER"
  mkdir -p "$(dirname "$ACCOUNTS_FILE")"
  if [ ! -f "$ACCOUNTS_FILE" ]; then
    echo "[User]" > "$ACCOUNTS_FILE"
  elif ! grep -q '^\[User\]' "$ACCOUNTS_FILE"; then
    echo "[User]" >> "$ACCOUNTS_FILE"
  fi
  sed -i '/^XSession=/d' "$ACCOUNTS_FILE"
  if grep -q '^Session=' "$ACCOUNTS_FILE"; then
    sed -i "s/^Session=.*/Session=$WAYLAND_SESSION/" "$ACCOUNTS_FILE"
  else
    echo "Session=$WAYLAND_SESSION" >> "$ACCOUNTS_FILE"
  fi
  echo -e "    ${GREEN}AccountsService: Session=$WAYLAND_SESSION (XSession entfernt)${NC}"

  # LightDM: Haupt-Config UND Drop-in (Drop-in überlebt raspi-config-Überschreibungen)
  LIGHTDM_CONF="/etc/lightdm/lightdm.conf"
  LIGHTDM_D="/etc/lightdm/lightdm.conf.d"
  LIGHTDM_DROPIN="$LIGHTDM_D/99-pi-installer-wayland.conf"

  mkdir -p "$LIGHTDM_D"
  cat > "$LIGHTDM_DROPIN" << LIGHTDMDROPIN
# PI-Installer: Wayland erzwingen (überschreibt raspi-config/rpd-x)
[Seat:*]
user-session=$WAYLAND_SESSION
autologin-session=$WAYLAND_SESSION
LIGHTDMDROPIN
  echo -e "    ${GREEN}LightDM Drop-in: $LIGHTDM_DROPIN → $WAYLAND_SESSION${NC}"

  if [ -f "$LIGHTDM_CONF" ]; then
    if grep -q '^user-session=' "$LIGHTDM_CONF"; then
      sed -i "s|^user-session=.*|user-session=$WAYLAND_SESSION|" "$LIGHTDM_CONF"
    fi
    if grep -q '^autologin-session=' "$LIGHTDM_CONF"; then
      sed -i "s|^autologin-session=.*|autologin-session=$WAYLAND_SESSION|" "$LIGHTDM_CONF"
    fi
    echo -e "    ${GREEN}LightDM: lightdm.conf angepasst${NC}"
  fi
else
  # Alle verfügbaren Sessions anzeigen
  echo -e "    ${YELLOW}Verfügbare Sessions:${NC}"
  ls /usr/share/wayland-sessions/*.desktop 2>/dev/null | xargs -I{} basename {} .desktop | sed 's/^/      /'
  ls /usr/share/xsessions/*.desktop 2>/dev/null | xargs -I{} basename {} .desktop | sed 's/^/      /' || true
  echo -e "    ${YELLOW}Manuell .dmrc setzen, z.B.: Session=rpd-labwc oder Session=labwc${NC}"
fi
echo ""

# --- 2. Gabriel Display-Configs sichern/entfernen ---
echo -e "${CYAN}[2] Display-Configs sichern (verhindern HDMI-Ausschaltung)${NC}"

TS="$(date +%Y%m%d-%H%M%S)"
BACKUP="$HOME_DIR/display-config-backup-$TS"
mkdir -p "$BACKUP"
chown "$USER:$(stat -c '%G' "$HOME_DIR")" "$BACKUP"

for path in ".config/monitors.xml" ".screenlayout"; do
  full="$HOME_DIR/$path"
  if [ -e "$full" ]; then
    mv "$full" "$BACKUP/$(basename "$path")" 2>/dev/null || true
    echo -e "    ${GREEN}Gesichert: $path → $BACKUP/${NC}"
  fi
done

# Kanshi-Verzeichnis sichern (falls vorhanden)
if [ -d "$HOME_DIR/.config/kanshi" ]; then
  mv "$HOME_DIR/.config/kanshi" "$BACKUP/kanshi" 2>/dev/null || true
  echo -e "    ${GREEN}Gesichert: .config/kanshi → $BACKUP/${NC}"
fi
echo ""

# --- 3. Kanshi config (Labwc/Wayfire – HDMI1 Hauptbildschirm, DSI Zusatzanzeige) ---
echo -e "${CYAN}[3] Kanshi config (HDMI1 Hauptbildschirm, DSI Zusatz)${NC}"

mkdir -p "$HOME_DIR/.config/kanshi"
cat > "$HOME_DIR/.config/kanshi/config" << 'KANSHICONF'
# PI-Installer: HDMI1 = Hauptbildschirm, DSI = Zusatzanzeige (90° nach links = Portrait)
profile DSI_HDMI {
  output HDMI-A-2 enable position 0,0
  output DSI-1 enable mode 800x480 position 3440,0 transform 90
  output HDMI-A-1 enable position 4240,0
}
KANSHICONF
chown -R "$USER:$(stat -c '%G' "$HOME_DIR")" "$HOME_DIR/.config/kanshi"
echo -e "    ${GREEN}kanshi/config erstellt${NC}"
echo ""

# --- 4. wayfire.ini (Dual Display, Fallback wenn Kanshi nicht greift) ---
echo -e "${CYAN}[4] wayfire.ini (Fallback)${NC}"

WF_INI="$HOME_DIR/.config/wayfire.ini"
mkdir -p "$(dirname "$WF_INI")"

# PI-Installer Block hinzufügen/aktualisieren
MARKER="# --- PI-Installer: Dual Display DSI+HDMI ---"
MARKER_END="# --- Ende PI-Installer Dual Display ---"

if [ -f "$WF_INI" ] && grep -q "$MARKER" "$WF_INI" 2>/dev/null; then
  sed -i "/$MARKER/,/$MARKER_END/d" "$WF_INI"
fi

{
  echo ""
  echo "$MARKER"
  echo "[output:HDMI-A-2]"
  echo "mode = auto"
  echo "position = 0,0"
  echo ""
  echo "[output:DSI-1]"
  echo "mode = 800x480"
  echo "position = 3440,0"
  echo "transform = 90"
  echo ""
  echo "[output:HDMI-A-1]"
  echo "mode = auto"
  echo "position = 2720,0"
  echo ""
  echo "[autostart]"
  echo "autostart_enable_hdmi = sh -c 'sleep 5 && wlr-randr --output HDMI-A-1 --on 2>/dev/null; wlr-randr --output HDMI-A-2 --on 2>/dev/null'"
  echo "$MARKER_END"
} >> "$WF_INI"

chown "$USER:$(stat -c '%G' "$HOME_DIR")" "$WF_INI"
echo -e "    ${GREEN}wayfire.ini aktualisiert${NC}"
echo ""

# --- 5. Enable-HDMI-Script aktualisieren (für X11 + Wayland) ---
echo -e "${CYAN}[5] Enable-HDMI-Script aktualisieren${NC}"
ENABLE_HDMI_SCRIPT="/usr/local/bin/pi-installer-enable-hdmi.sh"
if [ -f "$ENABLE_HDMI_SCRIPT" ]; then
  cat > "$ENABLE_HDMI_SCRIPT" << 'HDMISCRIPT'
#!/bin/sh
# PI-Installer: HDMI nach Desktop-Start einschalten (DSI+HDMI Dual Display)
sleep 20
if [ "$XDG_SESSION_TYPE" = "wayland" ] || [ -n "$WAYLAND_DISPLAY" ]; then
  wlr-randr --output HDMI-A-1 --on 2>/dev/null
  wlr-randr --output HDMI-A-2 --on 2>/dev/null
else
  export DISPLAY="${DISPLAY:-:0}"
  xrandr --output HDMI-1-2 --primary --auto --pos 0x0 2>/dev/null
  xrandr --output DSI-1 --auto --right-of HDMI-1-2 2>/dev/null
  xrandr --output HDMI-1-1 --auto --right-of DSI-1 2>/dev/null
fi
HDMISCRIPT
  chmod +x "$ENABLE_HDMI_SCRIPT"
  echo -e "    ${GREEN}Enable-Script aktualisiert: $ENABLE_HDMI_SCRIPT${NC}"
else
  echo -e "    ${YELLOW}Enable-Script nicht gefunden – zuerst setup-pi5-dual-display-dsi-hdmi0.sh ausführen${NC}"
fi
echo ""

# --- 6. Labwc-Fensterregel: Cursor auf HDMI starten ---
echo -e "${CYAN}[6] Labwc-Fensterregel: Cursor auf HDMI${NC}"
if [ -d "/usr/share/wayland-sessions" ] && ls /usr/share/wayland-sessions/*labwc* 1>/dev/null 2>&1; then
  if sudo -u "$USER" "$(dirname "$0")/add-labwc-cursor-to-hdmi.sh" 2>/dev/null; then
    echo -e "    ${GREEN}Labwc: Cursor öffnet auf HDMI-A-2 (Hauptbildschirm)${NC}"
  else
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    echo -e "    ${YELLOW}Manuell: $SCRIPT_DIR/add-labwc-cursor-to-hdmi.sh (als $USER)${NC}"
  fi
else
  echo -e "    ${YELLOW}Labwc nicht erkannt – Fensterregel übersprungen${NC}"
fi
echo ""

# --- 7. HDMI sofort aktivieren (falls X11 läuft) ---
echo -e "${CYAN}[7] HDMI sofort aktivieren (aktuelle X11-Session)${NC}"
XAUTH="$HOME_DIR/.Xauthority"
if [ -f "$XAUTH" ] && pgrep -u "$USER" -x Xorg >/dev/null 2>&1; then
  if sudo -u "$USER" DISPLAY=:0 XAUTHORITY="$XAUTH" xrandr --output HDMI-1-2 --primary --auto --pos 0x0 2>/dev/null; then
    sudo -u "$USER" DISPLAY=:0 XAUTHORITY="$XAUTH" xrandr --output DSI-1 --auto --right-of HDMI-1-2 2>/dev/null
    sudo -u "$USER" DISPLAY=:0 XAUTHORITY="$XAUTH" xrandr --output HDMI-1-1 --auto --right-of DSI-1 2>/dev/null
    echo -e "    ${GREEN}HDMI-1-1 und HDMI-1-2 aktiviert${NC}"
  else
    echo -e "    ${YELLOW}xrandr fehlgeschlagen (z.B. keine X-Session)${NC}"
  fi
else
  echo -e "    ${YELLOW}X11 nicht aktiv – HDMI nach Login/Neustart via Enable-Script${NC}"
fi
echo ""

echo -e "${GREEN}Fertig.${NC}"
echo ""
echo "Nächste Schritte:"
echo "  1. Neustart: sudo reboot"
echo "  2. Beim nächsten Login sollte Wayland (rpd-labwc) starten"
echo "  3. Falls weiterhin X11: sudo raspi-config → Advanced Options → A6 → Labwc wählen"
echo ""
echo "Backup der alten Configs: $BACKUP"
echo "Bei Problemen: mv $BACKUP/* ~/.config/  (als $USER)"
echo ""
echo "Cursor öffnet auf DSI (800x480)? Fensterregel setzen:"
echo "  ./scripts/add-labwc-cursor-to-hdmi.sh"
echo "  (Cursor startet dann auf HDMI-Hauptbildschirm)"