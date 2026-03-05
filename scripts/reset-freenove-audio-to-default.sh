#!/bin/bash
# PI-Installer: Freenove-Audio auf Standard zurücksetzen
#
# Entfernt alle PI-Installer-spezifischen Audio-Einstellungen (WirePlumber,
# Autostart), damit du von Null mit den richtigen Annahmen neu einrichten kannst.
# Kein X11, keine "Card 0"-Annahme – nur Zurücksetzen.
#
# Danach: docs/FREENOVE_AUDIO_TROUBLESHOOTING.md → "Freenove Audio von Null einrichten"
#
# Ausführung: ./scripts/reset-freenove-audio-to-default.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}=== Freenove-Audio auf Standard zurücksetzen ===${NC}"
echo ""
echo "Entfernt:"
echo "  - WirePlumber-Konfiguration für HDMI-A-1 (system + user)"
echo "  - Autostart 'Freenove Standard-Sink'"
echo "  - (Optional) WirePlumber-State für saubere Standard-Sink-Wahl)"
echo ""

# --- 1. System-WirePlumber-Konfiguration (sudo) ---
echo -e "${CYAN}[1] System-WirePlumber-Konfiguration:${NC}"
SYS_CONF="/etc/xdg/wireplumber/wireplumber.conf.d/50-alsa-hdmi-a1.conf"
if [ -f "$SYS_CONF" ]; then
  if [ -w "$SYS_CONF" ] 2>/dev/null || sudo -n true 2>/dev/null; then
    sudo rm -f "$SYS_CONF"
    echo -e "  ${GREEN}✓${NC} Entfernt: $SYS_CONF"
  else
    echo -e "  ${YELLOW}⚠${NC} Bitte manuell entfernen: sudo rm -f $SYS_CONF"
  fi
else
  echo "  (nicht vorhanden)"
fi
echo ""

# --- 2. User-WirePlumber-Konfiguration ---
echo -e "${CYAN}[2] Benutzer-WirePlumber-Konfiguration:${NC}"
USER_CONF_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/wireplumber/wireplumber.conf.d"
REMOVED=0
if [ -d "$USER_CONF_DIR" ]; then
  for f in "$USER_CONF_DIR"/50-alsa-hdmi-a1.conf "$USER_CONF_DIR"/51-freenove*.conf; do
    [ -f "$f" ] || continue
    rm -f "$f"
    echo -e "  ${GREEN}✓${NC} Entfernt: $f"
    REMOVED=1
  done
  [ "$REMOVED" = 0 ] && echo "  (keine PI-Installer-Configs vorhanden)"
  rmdir "$USER_CONF_DIR" 2>/dev/null || true
else
  echo "  (Verzeichnis nicht vorhanden)"
fi
echo ""

# --- 3. systemd-User-Service (HDMI-A-1 sehr früh) ---
echo -e "${CYAN}[3] systemd-User-Service (freenove-default-sink):${NC}"
SERVICE_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/freenove-default-sink.service"
if [ -f "$SERVICE_FILE" ]; then
  systemctl --user disable freenove-default-sink.service 2>/dev/null || true
  rm -f "$SERVICE_FILE"
  systemctl --user daemon-reload 2>/dev/null || true
  echo -e "  ${GREEN}✓${NC} Entfernt: $SERVICE_FILE"
else
  echo "  (nicht vorhanden)"
fi
echo ""

# --- 4. Autostart Freenove Standard-Sink ---
echo -e "${CYAN}[4] Autostart Freenove Standard-Sink:${NC}"
AUTOSTART="${XDG_CONFIG_HOME:-$HOME/.config}/autostart/pi-installer-freenove-default-sink.desktop"
if [ -f "$AUTOSTART" ]; then
  rm -f "$AUTOSTART"
  echo -e "  ${GREEN}✓${NC} Entfernt: $AUTOSTART"
else
  echo "  (nicht vorhanden)"
fi
echo ""

# --- 5. Optional: WirePlumber-State löschen (Standard-Sink wird neu gewählt) ---
echo -e "${CYAN}[5] WirePlumber-State (optional):${NC}"
STATE_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/wireplumber"
if [ -d "$STATE_DIR" ]; then
  STATE_FILES=$(find "$STATE_DIR" -name "*state*" -o -name "*default*" -o -name "*persist*" 2>/dev/null || true)
  if [ -n "$STATE_FILES" ]; then
    echo "  State-Dateien gefunden. Löschen für saubere Standard-Sink-Wahl?"
    echo "  (Danach: systemctl --user restart wireplumber)"
    read -p "  State löschen? [j/N]: " ans
    case "$ans" in
      [jJ]*)
        for f in $STATE_FILES; do [ -f "$f" ] && rm -f "$f" && echo "    Entfernt: $f"; done
        echo -e "  ${GREEN}✓${NC} State gelöscht"
        ;;
      *) echo "  Übersprungen." ;;
    esac
  else
    echo "  Keine State-Dateien gefunden."
  fi
else
  echo "  (State-Verzeichnis nicht vorhanden)"
fi
echo ""

echo -e "${GREEN}Fertig.${NC}"
echo ""
echo -e "${CYAN}=== Von Null einrichten (Wayland, richtige Annahmen) ===${NC}"
echo ""
echo "1. WirePlumber neu starten (als Benutzer, ohne sudo):"
echo "   systemctl --user restart wireplumber"
echo "   sleep 4"
echo ""
echo "2. HDMI-A-1 Konfiguration wieder anlegen (sudo nur für /etc):"
echo "   sudo ./scripts/configure-wireplumber-hdmi-a1.sh"
echo ""
echo "3. Als Benutzer: Sink aktivieren und Standard setzen:"
echo "   systemctl --user restart wireplumber"
echo "   sleep 4"
echo "   ./scripts/activate-hdmi-a1-sink.sh"
echo "   paplay /usr/share/sounds/alsa/Front_Left.wav"
echo ""
echo "4. Optional: HDMI-A-1 sehr früh + Standard-Sink nach Login:"
echo "   ./scripts/install-freenove-default-sink-autostart.sh"
echo "   (richtet systemd-User-Service + Autostart ein)"
echo ""
echo "Ausführlich: docs/FREENOVE_AUDIO_TROUBLESHOOTING.md (Abschnitt „Von Null einrichten“)"
echo ""
