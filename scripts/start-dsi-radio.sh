#!/bin/bash
# PI-Installer – DSI-Radio als eigenständige PyQt6-App (Freenove 4,3" DSI)
# Das Radio läuft als eigene PyQt-App; kein Frontend/Browser nötig.
# Fallback nur wenn PyQt6 fehlt: Browser mit Web-Ansicht (Backend + Frontend nötig).
#
# Verwendung:
#   ./scripts/start-dsi-radio.sh
#   oder direkt die native App: ./scripts/start-dsi-radio-native.sh
#
# Wayfire-Regel: Fenster mit Titel „PI-Installer DSI“ → DSI-1 (TFT; siehe docs/FREENOVE_TFT_DISPLAY.md)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
NATIVE_SCRIPT="$SCRIPT_DIR/start-dsi-radio-native.sh"

# 1. Native PyQt6-App starten, falls verfügbar (empfohlen: kein Frontend nötig, DSI-Platzierung zuverlässig)
if [ -x "$NATIVE_SCRIPT" ] && [ -f "$REPO_ROOT/apps/dsi_radio/dsi_radio.py" ]; then
  export PI_INSTALLER_DSI_PORTRAIT="${PI_INSTALLER_DSI_PORTRAIT:-1}"
  # Damit Wayfire-Regel (app_id "pi-installer-dsi-radio") greift: .desktop in Anwendungsmenü ablegen
  APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
  DESKTOP_DST="$APP_DIR/pi-installer-dsi-radio.desktop"
  if [ ! -f "$DESKTOP_DST" ]; then
    mkdir -p "$APP_DIR"
    cat > "$DESKTOP_DST" << DESKTOP
[Desktop Entry]
Type=Application
Name=DSI Radio (PI-Installer)
Comment=Internetradio auf dem Gehäuse-Display
Exec=$REPO_ROOT/scripts/start-dsi-radio.sh
Icon=applications-multimedia
Path=$REPO_ROOT
Terminal=false
Categories=Audio;Music;
DESKTOP
    chmod +x "$DESKTOP_DST" 2>/dev/null || true
  fi
  # Wayfire-Regeln sicherstellen (stumm), damit Fenster auf DSI-1 erscheint
  [ -x "$SCRIPT_DIR/ensure-dsi-window-rule.sh" ] && "$SCRIPT_DIR/ensure-dsi-window-rule.sh" >/dev/null 2>&1 || true
  if [ -d "$REPO_ROOT/apps/dsi_radio/.venv" ] && [ -f "$REPO_ROOT/apps/dsi_radio/.venv/bin/python" ]; then
    exec "$REPO_ROOT/apps/dsi_radio/.venv/bin/python" "$REPO_ROOT/apps/dsi_radio/dsi_radio.py" "$@"
  fi
  if python3 -c "import PyQt6" 2>/dev/null; then
    exec python3 "$REPO_ROOT/apps/dsi_radio/dsi_radio.py" "$@"
  fi
fi

# 2. Fallback: Browser mit Web-Ansicht (Backend 8000, Frontend 5173 oder 3001 müssen laufen)
if [ -n "$PI_INSTALLER_DSI_URL" ]; then
  FRONTEND_URL="$PI_INSTALLER_DSI_URL"
else
  # Port erkennung: Tauri/Vite-Dev = 5173, sonst Vite = 3001
  if ss -tuln 2>/dev/null | grep -q ':5173 '; then
    FRONTEND_URL="http://127.0.0.1:5173/?view=dsi-radio"
  elif ss -tuln 2>/dev/null | grep -qE ':3001 |:3002 '; then
    FRONTEND_URL="http://127.0.0.1:3001/?view=dsi-radio"
  else
    FRONTEND_URL="http://127.0.0.1:5173/?view=dsi-radio"
  fi
fi

BROWSER=""
for b in chromium chromium-browser chromium-wayland midori firefox firefox-esr epiphany; do
  if command -v "$b" >/dev/null 2>&1; then
    BROWSER="$b"
    break
  fi
done

if [ -z "$BROWSER" ]; then
  echo "Kein Browser gefunden. Für DSI-Radio ohne Web-Setup die native App einrichten:"
  echo "  cd $REPO_ROOT/apps/dsi_radio && pip install -r requirements.txt"
  echo "  ./scripts/start-dsi-radio-native.sh"
  exit 1
fi

echo "Starte DSI-Radio (Browser): $FRONTEND_URL"
echo "Hinweis: Fenster ggf. per Maus auf DSI ziehen. Oder native App nutzen: ./scripts/start-dsi-radio-native.sh"
# Wayfire-Regel sicherstellen, damit Fenster auf DSI-1 (TFT) erscheint
if [ -x "$SCRIPT_DIR/ensure-dsi-window-rule.sh" ]; then
  "$SCRIPT_DIR/ensure-dsi-window-rule.sh" >/dev/null 2>&1 || true
fi
echo ""

cd "$REPO_ROOT"

case "$BROWSER" in
  chromium|chromium-browser|chromium-wayland)
    exec "$BROWSER" --app="$FRONTEND_URL" --window-size=800,480 --window-position=0,0 2>/dev/null || \
    exec "$BROWSER" --app="$FRONTEND_URL" --window-position=0,0 2>/dev/null || \
    exec "$BROWSER" --app="$FRONTEND_URL" 2>/dev/null || true
    ;;
  midori)
    exec midori -e Fullscreen -a "$FRONTEND_URL" 2>/dev/null || exec midori "$FRONTEND_URL"
    ;;
  firefox|firefox-esr)
    exec "$BROWSER" -kiosk "$FRONTEND_URL" 2>/dev/null || exec "$BROWSER" "$FRONTEND_URL"
    ;;
  *)
    exec "$BROWSER" "$FRONTEND_URL"
    ;;
esac
