#!/bin/bash
# PI-Installer: HDMI-A-1 sehr früh + Autostart – Standard-Sink auf Gehäuselautsprecher
#
# Nach Neustart setzt WirePlumber den Standard-Sink auf HDMI-A-2 (Monitor).
# Dieses Skript richtet ein:
# 1. systemd-User-Service: Läuft direkt nach WirePlumber (sehr früh) und aktiviert
#    HDMI-A-1 sowie setzt ihn als Standard-Sink.
# 2. Autostart: Setzt den Standard-Sink nach Login nochmals (Fallback).
#
# Ausführung: ./scripts/install-freenove-default-sink-autostart.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EARLY_SCRIPT="$SCRIPT_DIR/set-freenove-default-sink-early.sh"
LOGIN_SCRIPT="$SCRIPT_DIR/set-freenove-default-sink-on-login.sh"
AUTOSTART_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"
DESKTOP_FILE="$AUTOSTART_DIR/pi-installer-freenove-default-sink.desktop"
SYSTEMD_USER_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
SERVICE_FILE="$SYSTEMD_USER_DIR/freenove-default-sink.service"

echo -e "${CYAN}=== Freenove Standard-Sink: sehr früh + Autostart ===${NC}"
echo ""

if [ ! -x "$EARLY_SCRIPT" ]; then
  chmod +x "$EARLY_SCRIPT" 2>/dev/null || true
fi
if [ ! -x "$LOGIN_SCRIPT" ]; then
  chmod +x "$LOGIN_SCRIPT" 2>/dev/null || true
fi

# --- 1. systemd-User-Service (HDMI-A-1 sehr früh nach WirePlumber) ---
echo -e "${CYAN}[1] systemd-User-Service (HDMI-A-1 sehr früh aktivieren):${NC}"
mkdir -p "$SYSTEMD_USER_DIR"
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=HDMI-A-1 (Gehäuselautsprecher) sehr früh als Standard-Sink setzen
After=wireplumber.service pipewire.service

[Service]
Type=oneshot
ExecStartPre=/bin/sleep 1
ExecStart=$EARLY_SCRIPT
RemainAfterExit=no

[Install]
WantedBy=default.target
EOF
echo -e "  ${GREEN}✓${NC} Service angelegt: $SERVICE_FILE"

if systemctl --user daemon-reload 2>/dev/null; then
  systemctl --user enable freenove-default-sink.service 2>/dev/null && echo -e "  ${GREEN}✓${NC} Service aktiviert (startet nach WirePlumber)"
else
  echo -e "  ${YELLOW}⚠${NC} systemctl --user daemon-reload fehlgeschlagen"
fi
echo ""

# --- 2. Autostart (Fallback, setzt Standard-Sink nochmals nach Login) ---
echo -e "${CYAN}[2] Autostart (Fallback):${NC}"
mkdir -p "$AUTOSTART_DIR"
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=Freenove Standard-Sink (Gehäuselautsprecher)
Comment=Setzt nach Login den Audio-Standard auf HDMI-A-1 (Fallback)
Exec=$LOGIN_SCRIPT 6
Hidden=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
EOF
echo -e "  ${GREEN}✓${NC} Autostart angelegt: $DESKTOP_FILE"
echo ""

echo "HDMI-A-1 wird jetzt sehr früh aktiviert (direkt nach WirePlumber),"
echo "bevor Anwendungen den Monitor-Sink übernehmen. Autostart setzt den"
echo "Standard-Sink nach Login zusätzlich."
echo ""
echo "Sofort testen (ohne Neustart):"
echo "  $EARLY_SCRIPT"
echo "  oder: $LOGIN_SCRIPT 2"
echo ""
echo "Entfernen:"
echo "  systemctl --user disable freenove-default-sink.service"
echo "  rm -f $SERVICE_FILE $DESKTOP_FILE"
echo "  systemctl --user daemon-reload"
echo ""
echo -e "${GREEN}Fertig.${NC}"
