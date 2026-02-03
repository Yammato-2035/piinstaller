#!/bin/bash
# Legt einen Desktop-Starter für „Backend neu starten“ auf dem Desktop ab.

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
START_SCRIPT="$PROJECT_ROOT/start-backend-desktop.sh"

# Startskript ausführbar machen
chmod +x "$START_SCRIPT" 2>/dev/null
chmod +x "$PROJECT_ROOT/start-backend.sh" 2>/dev/null

# Desktop-Ordner (englisch und/oder deutsch)
DESKTOPS=()
[ -d "$HOME/Desktop" ]      && DESKTOPS+=("$HOME/Desktop")
[ -d "$HOME/Schreibtisch" ] && DESKTOPS+=("$HOME/Schreibtisch")
[ ${#DESKTOPS[@]} -eq 0 ]   && DESKTOPS+=("$HOME")

for DESKTOP in "${DESKTOPS[@]}"; do
  DESKTOP_FILE="$DESKTOP/PI-Installer-Backend-starten.desktop"
  # Pfad in Anführungszeichen, damit Leerzeichen (z. B. "Software aus PI holen") funktionieren
  cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=PI-Installer Backend starten
Comment=Backend neu starten (Port 8000)
Exec="$START_SCRIPT"
Path=$PROJECT_ROOT
Icon=utilities-terminal
Terminal=true
Categories=Development;System;
EOF
  chmod +x "$DESKTOP_FILE"
  echo "✅ Desktop-Datei angelegt: $DESKTOP_FILE"
done

echo ""
echo "Doppelklick auf „PI-Installer Backend starten“ startet das Backend neu (im Terminal)."
