#!/bin/bash
# Skript zum Fixen der dist-Berechtigungen für Tauri Build

set -e

INSTALL_DIR="${1:-/opt/pi-installer}"
FRONTEND_DIR="$INSTALL_DIR/frontend"
DIST_DIR="$FRONTEND_DIR/dist"

echo "🔧 Fixe Berechtigungen für Tauri Build..."

if [ ! -d "$FRONTEND_DIR" ]; then
    echo "❌ Frontend-Verzeichnis nicht gefunden: $FRONTEND_DIR"
    exit 1
fi

# Aktueller Benutzer ermitteln
CURRENT_USER="${SUDO_USER:-$USER}"
if [ "$EUID" -eq 0 ] && [ -z "$SUDO_USER" ]; then
    echo "❌ Bitte mit sudo ausführen oder als normaler Benutzer"
    exit 1
fi

echo "📁 Entferne altes dist-Verzeichnis..."
sudo rm -rf "$DIST_DIR" 2>/dev/null || true

echo "✅ Berechtigungen gefixt. Du kannst jetzt bauen:"
echo "   cd $FRONTEND_DIR"
echo "   npm run tauri:build"
