#!/usr/bin/env bash
# PI-Installer – DSI-Radio-App lokal installieren (auf dem Pi ausführen)
# Nach git pull auf dem Pi: ./scripts/install-dsi-radio-local.sh
# Erstellt venv in apps/dsi_radio/.venv und installiert PyQt6.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DSI="$REPO_ROOT/apps/dsi_radio"
VENV="$DSI/.venv"

if [ ! -f "$DSI/dsi_radio.py" ]; then
  echo "Fehler: $DSI/dsi_radio.py nicht gefunden. Repo-Pfad: $REPO_ROOT"
  exit 1
fi

echo "Installiere DSI-Radio-App in $DSI ..."
python3 -m venv "$VENV" || { echo "Tipp: sudo apt install python3-venv"; exit 1; }
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r "$DSI/requirements.txt"
chmod +x "$REPO_ROOT/scripts/start-dsi-radio.sh" 2>/dev/null || true
chmod +x "$REPO_ROOT/scripts/start-dsi-radio-native.sh" 2>/dev/null || true

echo "Fertig. Starten: $REPO_ROOT/scripts/start-dsi-radio.sh"
if ! command -v cvlc >/dev/null 2>&1 && ! command -v mpv >/dev/null 2>&1 && ! command -v mpg123 >/dev/null 2>&1; then
  echo "Hinweis: Audio-Player fehlt. sudo apt install vlc  oder  sudo apt install mpv"
fi
