#!/bin/bash
# PI-Installer – Pi 5: Dual Display (DSI/CAM0 + HDMI) – Wayland/Wayfire
# Konfiguriert gleichzeitige Ausgabe auf:
#   - DSI-Display am internen Anschluss (CAM0)
#   - externer Monitor an HDMI (HDMI0 oder HDMI1)
#
# Voraussetzung: Wayland-Session (Pix/Wayfire) – auf Login-Bildschirm Session wählen.
# Führt vor den Änderungen ein Backup der config.txt und cmdline.txt durch.
# Auf dem Raspberry Pi mit sudo ausführen: sudo ./setup-pi5-dual-display-dsi-hdmi0.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

CONFIG_FILE="/boot/firmware/config.txt"
CONFIG_LEGACY="/boot/config.txt"
CMDLINE_FILE="/boot/firmware/cmdline.txt"
CMDLINE_LEGACY="/boot/cmdline.txt"
BACKUP_DIR="/boot/firmware"
MARKER_START="# --- PI-Installer: Dual Display DSI+HDMI0 (Pi 5) ---"
MARKER_END="# --- Ende PI-Installer Dual Display ---"

usage() {
  echo "Verwendung: sudo $0"
  echo ""
  echo "Konfiguriert Pi 5 für gleichzeitige Ausgabe:"
  echo "  - DSI-Display am internen Anschluss (CAM0)"
  echo "  - Monitor an HDMI0 oder HDMI1 (empfohlen: HDMI1)"
  echo ""
  echo "Erstellt Backup von config.txt und cmdline.txt vor den Änderungen."
  exit 1
}

# Root prüfen
if [ "$(id -u)" -ne 0 ]; then
  echo -e "${RED}Fehler: Bitte mit sudo ausführen: sudo $0${NC}"
  exit 1
fi

# Dateipfade ermitteln
[ -f "$CONFIG_FILE" ] || CONFIG_FILE="$CONFIG_LEGACY"
[ -f "$CMDLINE_FILE" ] || CMDLINE_FILE="$CMDLINE_LEGACY"

if [ ! -f "$CONFIG_FILE" ]; then
  echo -e "${RED}Fehler: config.txt nicht gefunden (weder $CONFIG_FILE noch $CONFIG_LEGACY)${NC}"
  exit 1
fi

if [ ! -f "$CMDLINE_FILE" ]; then
  echo -e "${RED}Fehler: cmdline.txt nicht gefunden${NC}"
  exit 1
fi

BACKUP_DIR="$(dirname "$CONFIG_FILE")"
TS="$(date +%Y%m%d-%H%M%S)"

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  Pi 5: Dual Display (DSI + HDMI)${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# --- 1. Backup ---
echo -e "${CYAN}[1] Backup der Konfigurationsdateien${NC}"
cp -a "$CONFIG_FILE" "${CONFIG_FILE}.backup.${TS}"
cp -a "$CMDLINE_FILE" "${CMDLINE_FILE}.backup.${TS}"
echo -e "    ${GREEN}Erstellt:${NC} ${CONFIG_FILE}.backup.${TS}"
echo -e "    ${GREEN}Erstellt:${NC} ${CMDLINE_FILE}.backup.${TS}"
echo ""

# --- 2. config.txt bearbeiten ---
echo -e "${CYAN}[2] config.txt anpassen${NC}"

# Vorherigen PI-Installer Dual-Display-Block entfernen
if grep -q "$MARKER_START" "$CONFIG_FILE" 2>/dev/null; then
  # Block zwischen MARKER_START und MARKER_END entfernen (inkl. Markern)
  sed -i "/$MARKER_START/,/$MARKER_END/d" "$CONFIG_FILE"
  echo "    Alter Dual-Display-Block entfernt."
fi

# Neuen Block anhängen (dtoverlay nur wenn noch nicht vorhanden)
NEED_DTOVERLAY="yes"
grep -q 'vc4-kms-v3d-pi5' "$CONFIG_FILE" 2>/dev/null && NEED_DTOVERLAY="no"

{
  echo ""
  echo "# --- PI-Installer: Dual Display DSI+HDMI0 (Pi 5) ---"
  echo "# DSI am internen Anschluss (CAM0) + Monitor an HDMI (0 oder 1) gleichzeitig nutzen"
  echo ""
  if [ "$NEED_DTOVERLAY" = "yes" ]; then
    echo "# Pi 5 Video-Treiber"
    echo "dtoverlay=vc4-kms-v3d-pi5"
    echo ""
  fi
  echo "# Dual Display: beide Ausgaben aktivieren"
} >> "$CONFIG_FILE"

cat >> "$CONFIG_FILE" << 'CONFIGBLOCK'
max_framebuffers=2

# Beide HDMI-Ports erzwingen
hdmi_force_hotplug=1

# HDMI0 (Port 1, näher USB-C) – kann von DSI priorisiert werden
[hdmi0]
hdmi_force_hotplug=1

# HDMI1 (Port 2) – oft stabiler bei DSI+HDMI Dual Display
[hdmi1]
hdmi_force_hotplug=1

# --- Ende PI-Installer Dual Display ---
CONFIGBLOCK

echo -e "    ${GREEN}Dual-Display-Einstellungen angehängt.${NC}"
echo ""

# --- 3. cmdline.txt bearbeiten ---
echo -e "${CYAN}[3] cmdline.txt anpassen${NC}"

if grep -qE '\bvc4\.force_hotplug=1\b' "$CMDLINE_FILE" 2>/dev/null; then
  echo "    vc4.force_hotplug=1 bereits vorhanden."
else
  # cmdline.txt ist meist eine einzige Zeile – Parameter ans Ende anhängen
  sed -i 's/$/ vc4.force_hotplug=1/' "$CMDLINE_FILE"
  echo -e "    ${GREEN}vc4.force_hotplug=1 hinzugefügt.${NC}"
fi
echo ""

# --- 4. Wayfire (Desktop) konfigurieren – DSI + HDMI explizit aktivieren ---
# Ohne dies nutzt Wayfire beim Start oft nur DSI; HDMI wird ausgeschaltet
# HDMI-A-2 (HDMI1) oft zuverlässiger, da DSI HDMI0 priorisieren kann
echo -e "${CYAN}[4] Wayfire wayfire.ini anpassen (DSI + HDMI aktiv)${NC}"

WF_MARKER="# --- PI-Installer: Dual Display DSI+HDMI ---"
WF_MARKER_END="# --- Ende PI-Installer Dual Display ---"

# wayfire.ini für alle Benutzer
for HOME_DIR in /home/*/ /root; do
  HOME_DIR="${HOME_DIR%/}"
  [ -d "$HOME_DIR" ] || continue
  WF_INI="$HOME_DIR/.config/wayfire.ini"
  mkdir -p "$(dirname "$WF_INI")"
  # Backup falls vorhanden
  [ -f "$WF_INI" ] && cp -a "$WF_INI" "${WF_INI}.backup.${TS}" 2>/dev/null || true
  # Alten PI-Installer-Block entfernen
  if [ -f "$WF_INI" ] && grep -q "$WF_MARKER" "$WF_INI" 2>/dev/null; then
    sed -i "/$WF_MARKER/,/$WF_MARKER_END/d" "$WF_INI"
  fi
  # Erweitertes Layout: DSI | HDMI-A-1 | HDMI-A-2 (kein Spiegeln, keine Überlappung)
  # DSI 800px breit, HDMI-A-1 bei 800, HDMI-A-2 bei 2720 (800+1920)
  {
    echo ""
    echo "$WF_MARKER"
    echo "# DSI + HDMI erweitert (nicht gespiegelt)"
    echo "[output:DSI-1]"
    echo "mode = auto"
    echo "position = 0,0"
    echo "transform = 90"
    echo ""
    echo "[output:HDMI-A-1]"
    echo "mode = auto"
    echo "position = 800,0"
    echo ""
    echo "[output:HDMI-A-2]"
    echo "mode = auto"
    echo "position = 2720,0"
    echo ""
    echo "# HDMI nach Session-Start explizit einschalten"
    echo "[autostart]"
    echo "autostart_enable_hdmi = sh -c 'sleep 5 && wlr-randr --output HDMI-A-1 --on 2>/dev/null; wlr-randr --output HDMI-A-2 --on 2>/dev/null'"
    echo "$WF_MARKER_END"
  } >> "$WF_INI"
  OWNER="$(stat -c '%U:%G' "$HOME_DIR" 2>/dev/null)" && chown "$OWNER" "$WF_INI" 2>/dev/null || true
  echo -e "    ${GREEN}wayfire.ini:${NC} $WF_INI"
done
echo ""

# --- 5. Autostart-Script + .desktop (HDMI explizit einschalten) ---
# Priorität: Wayland (wlr-randr), Fallback X11 (xrandr)
echo -e "${CYAN}[5] Autostart-Script (Wayland wlr-randr, Fallback xrandr)${NC}"

ENABLE_HDMI_SCRIPT="/usr/local/bin/pi-installer-enable-hdmi.sh"
cat > "$ENABLE_HDMI_SCRIPT" << 'HDMISCRIPT'
#!/bin/sh
# PI-Installer: HDMI nach Desktop-Start einschalten (DSI+HDMI Dual Display)
# 20 s Verzögerung – damit nach allem, was beim Login HDMI ausschaltet (X11)
sleep 20
# Session-Typ explizit prüfen (XDG_SESSION_TYPE ist zuverlässiger als wlr-randr Exit-Code)
if [ "$XDG_SESSION_TYPE" = "wayland" ] || [ -n "$WAYLAND_DISPLAY" ]; then
  wlr-randr --output HDMI-A-1 --on 2>/dev/null
  wlr-randr --output HDMI-A-2 --on 2>/dev/null
else
  # X11: HDMI1 Hauptbildschirm, DSI Zusatzanzeige
  export DISPLAY="${DISPLAY:-:0}"
  xrandr --output HDMI-1-2 --primary --auto --pos 0x0 2>/dev/null
  xrandr --output DSI-1 --auto --right-of HDMI-1-2 2>/dev/null
  xrandr --output HDMI-1-1 --auto --right-of DSI-1 2>/dev/null
fi
HDMISCRIPT
chmod +x "$ENABLE_HDMI_SCRIPT"
echo -e "    ${GREEN}Script erstellt:${NC} $ENABLE_HDMI_SCRIPT"

# Autostart: systemweit + pro Benutzer (damit Gabriel u.a. abgedeckt sind)
mkdir -p /etc/xdg/autostart
cat > /etc/xdg/autostart/pi-installer-enable-hdmi.desktop << DESKTOPFILE
[Desktop Entry]
Type=Application
Name=PI-Installer Enable HDMI (Dual Display)
Exec=$ENABLE_HDMI_SCRIPT
Hidden=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
DESKTOPFILE
echo -e "    ${GREEN}System-Autostart:${NC} /etc/xdg/autostart/pi-installer-enable-hdmi.desktop"

for HOME_DIR in /home/*/ /root; do
  HOME_DIR="${HOME_DIR%/}"
  [ -d "$HOME_DIR" ] || continue
  mkdir -p "$HOME_DIR/.config/autostart"
  DESKTOP="$HOME_DIR/.config/autostart/pi-installer-enable-hdmi.desktop"
  cat > "$DESKTOP" << DESKTOPFILE
[Desktop Entry]
Type=Application
Name=PI-Installer Enable HDMI (Dual Display)
Exec=$ENABLE_HDMI_SCRIPT
Hidden=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
DESKTOPFILE
  OWNER="$(stat -c '%U:%G' "$HOME_DIR" 2>/dev/null)" && chown "$OWNER" "$DESKTOP" 2>/dev/null || true
  echo -e "    ${GREEN}User-Autostart:${NC} $DESKTOP"
done
echo ""

echo -e "${GREEN}Konfiguration abgeschlossen.${NC}"
echo ""
echo "Nächster Schritt: Neustart ausführen:"
echo -e "  ${YELLOW}sudo reboot${NC}"
echo ""
echo "Nach dem Neustart sollten DSI-Display und HDMI-Monitor gleichzeitig arbeiten."
echo ""
echo -e "${YELLOW}Tipp: Falls HDMI am Port 1 (HDMI0) aus geht, Monitor an Port 2 (HDMI1) stecken.${NC}"
echo "Auf Pi 5 kann DSI HDMI0 priorisieren – HDMI1 ist dann oft zuverlässiger."
echo ""
echo "HDMI nutzt EDID-Auto (Auflösung/Hz automatisch, inkl. 4K@240Hz)."
echo ""
echo "Autostart: xrandr (X11) nach 20 s – läuft für alle Benutzer inkl. Gabriel."
echo ""
echo -e "${YELLOW}Wayland aktivieren: Abmelden → Session wählen (Zahnrad) → Pix (Wayland)${NC}"
