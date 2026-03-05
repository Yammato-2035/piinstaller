#!/bin/bash
# PI-Installer – DSI-Radio als native PyQt6-App (Freenove 4,3" DSI)
# Kein Frontend/Backend nötig. Fenstertitel „PI-Installer DSI Radio“ → Wayfire legt Fenster auf DSI-1 (TFT).
#
# Verwendung:
#   ./scripts/start-dsi-radio-native.sh
#
# Voraussetzung: PyQt6 installiert (siehe apps/dsi_radio/requirements.txt).
# Optional: Backend auf Port 8000 für Metadaten (Now Playing).
# DSI Portrait: PI_INSTALLER_DSI_PORTRAIT=1 (Fenster 480×800 für transform 90).

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_DIR="$REPO_ROOT/apps/dsi_radio"
VENV="$APP_DIR/.venv"

if [ ! -f "$APP_DIR/dsi_radio.py" ]; then
  echo "Fehler: $APP_DIR/dsi_radio.py nicht gefunden."
  exit 1
fi

# DSI im Portrait: Fenster 480×800 (transform 90)
export PI_INSTALLER_DSI_PORTRAIT="${PI_INSTALLER_DSI_PORTRAIT:-1}"

# Bevorzugt System-Python, wenn PyQt6 und GStreamer (gi) vorhanden (DSI Radio v2.0)
if python3 -c "import PyQt6" 2>/dev/null && python3 -c "import gi; gi.require_version('Gst', '1.0'); from gi.repository import Gst" 2>/dev/null; then
  exec python3 "$APP_DIR/dsi_radio.py" "$@"
fi

# Virtuelle Umgebung nutzen (venv sieht systemseitige GStreamer-Pakete nicht)
if [ -d "$VENV" ] && [ -f "$VENV/bin/python" ]; then
  exec "$VENV/bin/python" "$APP_DIR/dsi_radio.py" "$@"
fi

# System-Python nur mit PyQt6 (GStreamer fehlt → App zeigt Installationshinweis)
if python3 -c "import PyQt6" 2>/dev/null; then
  exec python3 "$APP_DIR/dsi_radio.py" "$@"
fi

echo "PyQt6 nicht gefunden. Bitte installieren:"
echo "  cd $APP_DIR && pip install -r requirements.txt"
echo "  oder: pip install PyQt6 requests"
exit 1
