#!/bin/bash
# QML / Qt Quick für Sabrina Tuner (DSI Radio QML-Prototyp) einrichten
#
# Installiert Systempakete, damit Qt und Qt Quick starten:
# - Qt 6 QML-Module (QtQuick, Controls, Layouts, Window)
# - XCB/Display-Abhängigkeiten für die Qt-Plattform (Fenster anzeigen)
#
# Aufruf:
#   sudo bash ./scripts/install-dsi-radio-qml-setup.sh
#
# Ohne sudo: Prüfung + Hinweise (keine Paketinstallation).
# Diagnose (zeigt genaue Fehler): apps/dsi_radio/.venv/bin/python apps/dsi_radio/check_qml.py

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DSI_RADIO_DIR="$REPO_ROOT/apps/dsi_radio"

echo "Sabrina Tuner – Qt / Qt Quick Setup"
echo "===================================="
echo ""

# 1) Venv
if [ ! -d "$DSI_RADIO_DIR/.venv" ]; then
  echo "Hinweis: Venv nicht gefunden. Zuerst ausführen:"
  echo "  sudo bash $REPO_ROOT/scripts/install-dsi-radio-setup.sh"
  echo ""
  exit 1
fi

PYTHON="$DSI_RADIO_DIR/.venv/bin/python"
if [ ! -x "$PYTHON" ]; then
  echo "Venv-Python nicht gefunden: $PYTHON"
  exit 1
fi

# 2) Diagnose: Läuft Qt/QML?
echo "[1] Qt / Qt Quick prüfen (mit Display) …"
echo "    Führe aus: $PYTHON $DSI_RADIO_DIR/check_qml.py"
echo ""
if ! "$PYTHON" "$DSI_RADIO_DIR/check_qml.py" 2>&1; then
  echo ""
  echo ">>> Qt oder Qt Quick starten nicht. Siehe Fehler oben."
  echo "    Oft hilft: Systempakete installieren (mit sudo, siehe [2])."
  echo ""
fi

# 3) Mit sudo: alle nötigen Pakete installieren
if [ "$(id -u)" -ne 0 ]; then
  echo "[2] Systempakete installieren (Qt 6 + Anzeige):"
  echo "    sudo bash $0"
  echo ""
  echo "    Installiert werden u. a.:"
  echo "    - libqt6qml6, qml6-module-qtquick, qml6-module-qtquick-controls,"
  echo "      qml6-module-qtquick-layouts, qml6-module-qtquick-window2"
  echo "    - libxcb-cursor0, libxcb-xinerama0, libxkbcommon0 (Qt-Plattform)"
  echo ""
  exit 0
fi

echo "[2] Systempakete für Qt 6 und Anzeige installieren …"
apt-get update -qq 2>/dev/null || true

# Qt 6 QML-Module (für QML-Prototyp)
apt-get install -y --no-install-recommends \
  libqt6qml6 \
  qml6-module-qtquick \
  qml6-module-qtquick-controls \
  qml6-module-qtquick-layouts \
  qml6-module-qtquick-window2 \
  2>/dev/null || true

# XCB / Anzeige – oft nötig, damit Qt-Fenster erscheinen (Plattform-Plugin xcb)
apt-get install -y --no-install-recommends \
  libxcb-cursor0 \
  libxcb-xinerama0 \
  libxkbcommon0 \
  libxkbcommon-x11-0 \
  libxcb-icccm4 \
  libxcb-image0 \
  libxcb-keysyms1 \
  libxcb-randr0 \
  libxcb-render-util0 \
  libxcb-shape0 \
  libxcb-xfixes0 \
  2>/dev/null || true

# Falls Wayland: Qt Wayland (optional)
apt-get install -y --no-install-recommends \
  libqt6waylandclient6 \
  2>/dev/null || true

echo "    Pakete installiert."
echo ""

# 4) Erneuter Check
echo "[3] Erneuter Qt-Check …"
if "$PYTHON" "$DSI_RADIO_DIR/check_qml.py" 2>&1; then
  echo ""
  echo "Qt / Qt Quick sind bereit."
else
  echo ""
  echo "Hinweis: Falls weiterhin Fehler (z. B. kein Display):"
  echo "  - App nur mit angemeldeter grafischer Sitzung starten (nicht per SSH ohne -X)."
  echo "  - Oder: export QT_QPA_PLATFORM=offscreen  (nur zum Testen ohne Fenster)."
fi

echo ""
echo "QML-Prototyp starten:"
echo "  $REPO_ROOT/scripts/start-dsi-radio-qml.sh"
echo ""
