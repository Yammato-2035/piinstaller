#!/usr/bin/env bash
# PI-Installer – DSI-Radio-App direkt auf dem Pi installieren
# Wird vom Laptop aus per SSH ausgeführt: installiert venv, PyQt6 und optional vlc-nox auf dem Pi.
#
# Verwendung (vom Laptop):
#   ./scripts/install-dsi-radio-on-pi.sh [PI-HOST]
#   PI_HOST=pi5-gg.local ./scripts/install-dsi-radio-on-pi.sh
#
# Voraussetzung: SSH-Zugriff auf den Pi (z. B. ssh pi), Repo auf dem Pi (z. B. ~/Documents/PI-Installer).

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

PI_HOST="${PI_HOST:-${1:-pi}}"
# Auf dem Pi: Repo-Pfad (von hier aus als Literal übergeben, auf dem Pi wird $HOME expandiert)
REPO_ON_PI="${PI_INSTALLER_REPO_ON_PI:-\$HOME/Documents/PI-Installer}"

echo -e "${CYAN}Installiere DSI-Radio-App auf dem Pi (${PI_HOST})...${NC}"
echo ""

# Auf dem Pi ausführen (Repo-Pfad als $1, wird per eval expandiert)
REMOTE_SCRIPT='
set -e
REPO=$(eval echo "${1:-$HOME/Documents/PI-Installer}")
DSI="$REPO/apps/dsi_radio"
VENV="$DSI/.venv"

if [ ! -f "$DSI/dsi_radio.py" ]; then
  echo "Fehler: $DSI/dsi_radio.py nicht gefunden. Repo auf dem Pi vorhanden? Pfad: $REPO"
  exit 1
fi

echo "Repo: $REPO"
echo "Erstelle venv in $DSI/.venv ..."
python3 -m venv "$VENV" 2>/dev/null || { echo "Hinweis: python3-venv ggf. installieren: sudo apt install python3-venv"; exit 1; }
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r "$DSI/requirements.txt"
echo "PyQt6 DSI-Radio installiert."

chmod +x "$REPO/scripts/start-dsi-radio.sh" 2>/dev/null || true
chmod +x "$REPO/scripts/start-dsi-radio-native.sh" 2>/dev/null || true

if ! command -v cvlc >/dev/null 2>&1 && ! command -v mpv >/dev/null 2>&1 && ! command -v mpg123 >/dev/null 2>&1; then
  echo ""
  echo "Hinweis: Kein Audio-Player (cvlc/mpv/mpg123). Für Wiedergabe: sudo apt install vlc  oder  sudo apt install mpv"
fi
echo ""
echo "Starten auf dem Pi: $REPO/scripts/start-dsi-radio.sh"
'

# SSH: Repo-Pfad übergeben (z. B. $HOME/Documents/PI-Installer, wird auf dem Pi expandiert)
ssh "$PI_HOST" "bash -s" -- "$REPO_ON_PI" <<< "$REMOTE_SCRIPT"

echo -e "${GREEN}DSI-Radio-App auf dem Pi installiert.${NC}"
echo ""
echo "Auf dem Pi starten:"
echo "  cd ~/Documents/PI-Installer && ./scripts/start-dsi-radio.sh"
echo ""
echo "Pi nicht erreichbar? Installation direkt auf dem Pi ausführen:"
echo "  ssh $PI_HOST   # dann auf dem Pi:"
echo "  cd ~/Documents/PI-Installer"
echo "  python3 -m venv apps/dsi_radio/.venv"
echo "  apps/dsi_radio/.venv/bin/pip install -r apps/dsi_radio/requirements.txt"
echo "  ./scripts/start-dsi-radio.sh"
echo ""
