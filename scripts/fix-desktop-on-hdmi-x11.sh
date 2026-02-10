#!/bin/bash
# PI-Installer: Desktop/Hintergrund auf HDMI (Primary) neu anzeigen
# Als Benutzer ausführen (nicht sudo): ./scripts/fix-desktop-on-hdmi-x11.sh
#
# Problem: Taskleiste ist auf HDMI-1-2, aber Desktop-Icons und Hintergrund erscheinen
# auf DSI-1 (LXDE/PCManFM nutzt oft den linkesten Monitor für den Hauptdesktop).
# Dieses Script startet den PCManFM-Desktop neu, damit er nach xrandr-Primary (HDMI)
# neu ausgerichtet wird.
#
# Siehe auch: apply-dual-display-x11-delayed.sh (macht das automatisch ~30 s nach Login)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-${HOME:-/home/gabrielglienke}/.Xauthority}"

echo -e "${CYAN}PCManFM-Desktop neu starten (Desktop/Hintergrund auf Primary/HDMI)${NC}"
echo ""

if ! command -v pcmanfm >/dev/null 2>&1; then
  echo -e "${RED}pcmanfm nicht gefunden.${NC}"
  exit 1
fi

# Profil ermitteln (LXDE-pi auf Pi OS, sonst default)
PROFILE="default"
for p in LXDE-pi default; do
  if [ -d "${XDG_CONFIG_HOME:-$HOME/.config}/pcmanfm/$p" ]; then
    PROFILE="$p"
    break
  fi
done

killall pcmanfm 2>/dev/null || true
sleep 1
pcmanfm --desktop --profile "$PROFILE" --display "$DISPLAY" &

echo -e "${GREEN}Fertig. PCManFM-Desktop wurde neu gestartet.${NC}"
echo "Falls Desktop/Hintergrund weiterhin auf DSI erscheint, ist das eine bekannte LXDE/PCManFM-Einschränkung (linkester Monitor = Hauptdesktop)."
echo ""
