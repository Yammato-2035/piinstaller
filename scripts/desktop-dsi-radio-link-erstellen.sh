#!/bin/bash
# Erstellt eine Desktop-Verknüpfung zu Sabrina Tuner (DSI Radio)
# Nutzen, wenn der Dateimanager „Link erstellen“ nicht anbietet
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DESKTOP="${XDG_DESKTOP_DIR:-$HOME/Desktop}"
LINK_NAME="Sabrina Tuner (DSI Radio).desktop"

mkdir -p "$DESKTOP"
cat > "$DESKTOP/$LINK_NAME" << EOF
[Desktop Entry]
Type=Application
Name=Sabrina Tuner (DSI Radio)
Comment=Internetradio – DSI Radio starten
Exec=$REPO_ROOT/start-dsi-radio.sh
Path=$REPO_ROOT
Icon=applications-multimedia
Terminal=false
Categories=Audio;Music;
EOF
chmod +x "$DESKTOP/$LINK_NAME"
echo "Verknüpfung erstellt: $DESKTOP/$LINK_NAME"
echo "Sabrina Tuner kann jetzt per Doppelklick auf dem Desktop gestartet werden."
