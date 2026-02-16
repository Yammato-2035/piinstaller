#!/bin/bash
# Sabrina Tuner – QML-Prototyp starten (gleiches venv wie Widgets-Version)
SCRIPT_PATH="$0"
if [ -L "$SCRIPT_PATH" ]; then
  SCRIPT_PATH="$(readlink -f "$SCRIPT_PATH" 2>/dev/null)" || SCRIPT_PATH="$0"
fi
[ -z "$SCRIPT_PATH" ] && SCRIPT_PATH="$0"
REPO_ROOT="$(cd "$(dirname "$SCRIPT_PATH")/.." && pwd)"
VENV_PYTHON="$REPO_ROOT/apps/dsi_radio/.venv/bin/python"
APP_MAIN="$REPO_ROOT/apps/dsi_radio/dsi_radio_qml.py"
if [ ! -f "$VENV_PYTHON" ] || [ ! -f "$APP_MAIN" ]; then
  echo "Sabrina Tuner QML: Repo nicht gefunden. Bitte aus piinstaller-Ordner starten."
  exit 1
fi
cd "$REPO_ROOT"
echo "Starte Sabrina Tuner (QML) … (Beenden: Fenster schließen oder Strg+C)"
exec "$VENV_PYTHON" "$APP_MAIN" "$@"
