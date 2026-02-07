#!/usr/bin/env bash
# PI-Installer – DSI-Display 90° nach links (Portrait) unter Wayland
# Setzt für DSI-1 „transform 90“ (90° gegen Uhrzeigersinn) in Kanshi und wayfire.ini.
# Nur das DSI-Display wird gedreht, HDMI bleibt unverändert.
#
# Verwendung (als Benutzer, der die Wayland-Session nutzt):
#   ./freenove-dsi-rotate-portrait.sh
#   oder mit sudo für einen anderen Benutzer: sudo -u gabrielglienke ./freenove-dsi-rotate-portrait.sh
#
# Nach dem Lauf: Kanshi neu starten oder einmal abmelden/anmelden.

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Benutzer: aktueller User oder SUDO_USER bei sudo
TARGET_USER="${SUDO_USER:-$USER}"
if [ -z "$TARGET_USER" ] || [ "$TARGET_USER" = "root" ]; then
  TARGET_USER="$(logname 2>/dev/null)" || TARGET_USER="$USER"
fi
HOME_DIR="${HOME:-/home/$TARGET_USER}"
[ -d "$HOME_DIR" ] || HOME_DIR="/home/$TARGET_USER"

KANSHI_CFG="$HOME_DIR/.config/kanshi/config"
WF_INI="$HOME_DIR/.config/wayfire.ini"

echo -e "${CYAN}DSI-Display: 90° nach links (Portrait)${NC}"
echo "Benutzer: $TARGET_USER"
echo ""

# --- 1. Kanshi: DSI-1 transform 90 ---
if [ -f "$KANSHI_CFG" ]; then
  if grep -q "DSI-1.*transform 90" "$KANSHI_CFG"; then
    echo -e "${GREEN}[Kanshi] DSI-1 hat bereits transform 90.${NC}"
  else
    # „output DSI-1 enable …“ um „transform 90“ ergänzen (oder bestehendes transform ersetzen)
    sed -i.bak -E 's/(output DSI-1 enable[^ \t]*)([ \t]transform[ \t][0-9]+)?/\1 transform 90/' "$KANSHI_CFG"
    echo -e "${GREEN}[Kanshi] DSI-1 auf transform 90 gesetzt: $KANSHI_CFG${NC}"
  fi
else
  mkdir -p "$(dirname "$KANSHI_CFG")"
  cat > "$KANSHI_CFG" << 'KANSHI'
# PI-Installer: DSI Portrait (90° nach links)
profile default {
  output DSI-1 enable mode 800x480 transform 90
}
KANSHI
  chown "$TARGET_USER:$(stat -c '%G' "$HOME_DIR" 2>/dev/null || echo "$TARGET_USER")" "$KANSHI_CFG" 2>/dev/null || true
  echo -e "${GREEN}[Kanshi] Konfiguration angelegt: $KANSHI_CFG${NC}"
fi

# --- 2. wayfire.ini: [output:DSI-1] transform = 90 ---
if [ -f "$WF_INI" ]; then
  if grep -A5 "\[output:DSI-1\]" "$WF_INI" | grep -q "transform.*90"; then
    echo -e "${GREEN}[wayfire.ini] DSI-1 hat bereits transform = 90.${NC}"
  elif grep -q "\[output:DSI-1\]" "$WF_INI"; then
    # Nach "position = ..." unter [output:DSI-1] Zeile "transform = 90" einfügen (nur erste Treffer)
    awk '
      /^\[output:DSI-1\]/ { in_dsi=1; print; next }
      in_dsi && /^position = / && !done { print; print "transform = 90"; done=1; next }
      /^\[/ && in_dsi { in_dsi=0; done=0 }
      { print }
    ' "$WF_INI" > "${WF_INI}.tmp" && mv "${WF_INI}.tmp" "$WF_INI"
    echo -e "${GREEN}[wayfire.ini] DSI-1 transform = 90 gesetzt.${NC}"
  else
    echo -e "${YELLOW}[wayfire.ini] Kein [output:DSI-1] gefunden – ggf. fix-gabriel-dual-display-wayland.sh ausführen.${NC}"
  fi
else
  echo -e "${YELLOW}[wayfire.ini] Nicht gefunden: $WF_INI${NC}"
fi

echo ""
echo "Nächste Schritte:"
echo "  • Einmal abmelden und wieder anmelden (damit Kanshi/Wayfire die neue Config laden),"
echo "  • oder Kanshi neu starten: killall kanshi 2>/dev/null; kanshi &"
echo ""
echo "Sofort testen (bleibt bis zum Neustart der Session):"
echo "  wlr-randr --output DSI-1 --transform 90"
