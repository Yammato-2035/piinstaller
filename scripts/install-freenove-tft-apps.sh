#!/usr/bin/env bash
# PI-Installer – Freenove TFT Apps Installation
# Richtet alles ein, damit Internetradio, Dashboard etc. auf dem DSI-Display laufen.
#
# - I2C aktivieren, Benutzer in i2c-Gruppe
# - i2c-tools, Chromium installieren
# - Wayfire-Fensterregel: Fenster mit Titel „PI-Installer DSI“ auf DSI-1 (TFT)
# - Desktop-Verknüpfung „DSI Radio“
# - Optional: Standard-Audio auf Gehäuse-Lautsprecher
#
# Auf dem Raspberry Pi mit sudo ausführen:
#   sudo ./scripts/install-freenove-tft-apps.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REAL_USER="${SUDO_USER:-$USER}"
HOME_DIR="/home/$REAL_USER"
[ "$REAL_USER" = "root" ] && HOME_DIR="/root"

usage() {
  echo "Verwendung: sudo $0"
  echo ""
  echo "Installiert alle Voraussetzungen für PI-Installer TFT-Apps auf dem Freenove-Gehäuse."
  exit 1
}

if [ "$(id -u)" -ne 0 ]; then
  echo -e "${RED}Bitte mit sudo ausführen: sudo $0${NC}"
  exit 1
fi

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  Freenove TFT Apps – Installation${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# --- 1. I2C aktivieren ---
echo -e "${CYAN}[1] I2C aktivieren${NC}"
if command -v raspi-config >/dev/null 2>&1; then
  raspi-config nonint do_i2c 0 2>/dev/null || true
  echo -e "    ${GREEN}raspi-config: I2C aktiviert${NC}"
else
  CONFIG="/boot/firmware/config.txt"
  [ -f "$CONFIG" ] || CONFIG="/boot/config.txt"
  if [ -f "$CONFIG" ] && ! grep -q '^dtparam=i2c_arm=on' "$CONFIG" 2>/dev/null; then
    echo "dtparam=i2c_arm=on" >> "$CONFIG"
    echo -e "    ${GREEN}config.txt: I2C ergänzt (Neustart nötig)${NC}"
  fi
fi

# --- 2. Benutzer in i2c-Gruppe ---
echo -e "${CYAN}[2] Benutzer in Gruppe i2c${NC}"
if getent group i2c >/dev/null 2>&1; then
  if ! groups "$REAL_USER" 2>/dev/null | grep -q '\bi2c\b'; then
    usermod -aG i2c "$REAL_USER"
    echo -e "    ${GREEN}$REAL_USER zu Gruppe i2c hinzugefügt${NC}"
  else
    echo -e "    ${GREEN}$REAL_USER bereits in i2c${NC}"
  fi
else
  echo -e "    ${YELLOW}Gruppe i2c nicht gefunden (i2c-tools installieren)${NC}"
fi

# --- 3. Pakete installieren ---
echo -e "${CYAN}[3] Pakete installieren (i2c-tools, chromium, GStreamer für DSI Radio)${NC}"
apt-get update -qq
apt-get install -y i2c-tools
if ! command -v chromium >/dev/null 2>&1 && ! command -v chromium-browser >/dev/null 2>&1; then
  apt-get install -y chromium || apt-get install -y chromium-browser || echo -e "    ${YELLOW}Chromium manuell installieren: sudo apt install chromium${NC}"
else
  echo -e "    ${GREEN}Chromium bereits installiert${NC}"
fi
# GStreamer + Python-Bindings (gi) für DSI-Radio (MP3 + AAC z. B. NDR 1, WDR 2)
apt-get install -y --no-install-recommends \
  python3-gi \
  gir1.2-gstreamer-1.0 \
  gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad \
  gstreamer1.0-pulseaudio \
  gstreamer1.0-libav \
  || echo -e "    ${YELLOW}GStreamer-Pakete teilweise fehlgeschlagen – DSI Radio: sudo $REPO_ROOT/scripts/install-dsi-radio-setup.sh${NC}"

# --- 4. Wayfire-Fensterregel für DSI ---
echo -e "${CYAN}[4] Wayfire-Fensterregel (DSI-Platzierung)${NC}"
WF_INI="$HOME_DIR/.config/wayfire.ini"
MARKER="# --- PI-Installer: DSI-Fensterregel ---"
MARKER_END="# --- Ende PI-Installer DSI ---"
# Zwei getrennte Regeln (app_id + title), damit start_on_output DSI-1 zuverlässig greift
RULE_APP='dsi_pi_installer_app = on created if app_id is "pi-installer-dsi-radio" then start_on_output "DSI-1"'
RULE_TITLE='dsi_pi_installer_title = on created if title contains "PI-Installer DSI" then start_on_output "DSI-1"'

mkdir -p "$(dirname "$WF_INI")"
if [ -f "$WF_INI" ] && grep -q "$MARKER" "$WF_INI" 2>/dev/null; then
  sed -i "/$MARKER/,/$MARKER_END/d" "$WF_INI"
fi
{
  echo ""
  echo "$MARKER"
  echo "# DSI-Radio: Fenster beim Start auf DSI-1 (TFT) legen"
  echo "[window-rules]"
  echo "$RULE_APP"
  echo "$RULE_TITLE"
  echo "$MARKER_END"
} >> "$WF_INI"
chown "$REAL_USER:$(id -gn "$REAL_USER")" "$WF_INI" 2>/dev/null || true
echo -e "    ${GREEN}wayfire.ini: $WF_INI${NC}"

# --- 5. Desktop-Verknüpfung DSI Radio (in Ordner PI-Installer) ---
echo -e "${CYAN}[5] Desktop-Verknüpfung 'DSI Radio'${NC}"
DESKTOP_DIR="$HOME_DIR/Desktop"
LAUNCHER_DIR="$DESKTOP_DIR/PI-Installer"
mkdir -p "$LAUNCHER_DIR"
DESKTOP_FILE="$LAUNCHER_DIR/DSI-Radio.desktop"
cat > "$DESKTOP_FILE" << DESKTOP
[Desktop Entry]
Type=Application
Name=DSI Radio
Comment=Eigenständige PyQt6-Radio-App – Internetradio (Freenove-TFT/DSI)
Exec=$REPO_ROOT/scripts/start-dsi-radio.sh
Path=$REPO_ROOT
Icon=applications-multimedia
Terminal=false
Categories=Audio;Music;
DESKTOP
chown "$REAL_USER:$(id -gn "$REAL_USER")" "$DESKTOP_FILE"
chmod +x "$DESKTOP_FILE"
echo -e "    ${GREEN}Erstellt: $DESKTOP_FILE${NC}"
# Für Portal/Wayfire app_id: .desktop auch in Anwendungsmenü (damit „App info not found“ entfällt)
APP_DIR="$HOME_DIR/.local/share/applications"
mkdir -p "$APP_DIR"
cp "$DESKTOP_FILE" "$APP_DIR/pi-installer-dsi-radio.desktop" 2>/dev/null && chown "$REAL_USER:$(id -gn "$REAL_USER")" "$APP_DIR/pi-installer-dsi-radio.desktop" && \
  echo -e "    ${GREEN}Anwendungsmenü: $APP_DIR/pi-installer-dsi-radio.desktop${NC}" || true

# --- 6. DSI-Radio: native PyQt6-App (empfohlen, kein Frontend nötig) ---
echo -e "${CYAN}[6] DSI-Radio native App (PyQt6 + GStreamer)${NC}"
DSI_RADIO_DIR="$REPO_ROOT/apps/dsi_radio"
DSI_VENV="$DSI_RADIO_DIR/.venv"
if [ -f "$DSI_RADIO_DIR/dsi_radio.py" ] && [ -f "$DSI_RADIO_DIR/requirements.txt" ]; then
  if [ ! -d "$DSI_VENV" ] || [ ! -f "$DSI_VENV/bin/python" ]; then
    # Mit --system-site-packages, damit python3-gi/GStreamer (aus Schritt 3) in der Venv sichtbar ist
    sudo -u "$REAL_USER" python3 -m venv --system-site-packages "$DSI_VENV" 2>/dev/null || true
  fi
  if [ -f "$DSI_VENV/bin/pip" ]; then
    sudo -u "$REAL_USER" "$DSI_VENV/bin/pip" install -q -r "$DSI_RADIO_DIR/requirements.txt" 2>/dev/null && \
      echo -e "    ${GREEN}PyQt6 DSI-Radio installiert (apps/dsi_radio/.venv)${NC}" || \
      echo -e "    ${YELLOW}PyQt6 manuell: cd $DSI_RADIO_DIR && pip install -r requirements.txt${NC}"
  else
    echo -e "    ${YELLOW}Venv fehlgeschlagen. Manuell: cd $DSI_RADIO_DIR && python3 -m venv --system-site-packages .venv && .venv/bin/pip install -r requirements.txt${NC}"
  fi
  echo -e "    ${GREEN}Bei 'No module named gi': sudo $REPO_ROOT/scripts/install-dsi-radio-setup.sh${NC}"
else
  echo -e "    ${YELLOW}apps/dsi_radio nicht gefunden, Browser-Fallback wird genutzt${NC}"
fi
chmod +x "$REPO_ROOT/scripts/start-dsi-radio.sh" 2>/dev/null || true
chmod +x "$REPO_ROOT/scripts/start-dsi-radio-native.sh" 2>/dev/null || true

# --- 7. Audio-Hinweis ---
echo ""
echo -e "${CYAN}[7] Audio (Gehäuse-Lautsprecher)${NC}"
echo -e "    Standard-Ausgabe in Einstellungen → Sound setzen."
echo -e "    Oder: pavucontrol → Ausgabegerät wählen."
echo ""

echo -e "${GREEN}=== Installation abgeschlossen ===${NC}"
echo ""
echo "Nächste Schritte:"
echo "  1. Abmelden und wieder anmelden (für i2c-Gruppe)"
echo "  2. PI-Installer starten: ./start-backend.sh + ./start-frontend.sh"
echo "  3. DSI Radio: Doppelklick auf Desktop-Icon oder ./scripts/start-dsi-radio.sh"
echo "     (Bevorzugt native PyQt6-App; Fallback: Browser, wenn Frontend läuft.)"
echo ""
echo "Fenster mit 'PI-Installer DSI' im Titel werden automatisch auf DSI-1 (TFT) angezeigt."
echo "DSI Radio nutzt GStreamer. Falls 'No module named gi': sudo ./scripts/install-dsi-radio-setup.sh"
echo ""
