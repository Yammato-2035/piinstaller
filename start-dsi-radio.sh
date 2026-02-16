#!/bin/bash
# Sabrina Tuner / DSI Radio starten (nutzt venv mit PyQt6)
# Repo-Root aus Skript-Pfad (Symlinks aufgelöst), damit Start aus beliebigem Ordner/Desktop funktioniert
SCRIPT_PATH="$0"
if [ -L "$SCRIPT_PATH" ]; then
  SCRIPT_PATH="$(readlink -f "$SCRIPT_PATH" 2>/dev/null)" || SCRIPT_PATH="$0"
fi
[ -z "$SCRIPT_PATH" ] && SCRIPT_PATH="$0"
REPO_ROOT="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
VENV_PYTHON="$REPO_ROOT/apps/dsi_radio/.venv/bin/python"
APP_MAIN="$REPO_ROOT/apps/dsi_radio/dsi_radio.py"
if [ ! -f "$VENV_PYTHON" ] || [ ! -f "$APP_MAIN" ]; then
  echo "Sabrina Tuner: Repo nicht gefunden. Bitte starten Sie das Skript aus dem piinstaller-Ordner oder legen Sie einen Link (nicht eine Kopie) auf den Desktop."
  echo "Erwartet: $APP_MAIN"
  if command -v zenity &>/dev/null; then zenity --error --text="Sabrina Tuner: Bitte Link auf start-dsi-radio.sh (aus dem piinstaller-Ordner) auf den Desktop legen, keine Kopie."; fi
  exit 1
fi
cd "$REPO_ROOT"
exec "$VENV_PYTHON" "$APP_MAIN" "$@"
