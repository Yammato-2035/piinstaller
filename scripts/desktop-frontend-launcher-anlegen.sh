#!/bin/bash
# Legt Desktop-Starter für das Frontend auf dem Desktop ab:
#   - PI-Installer Frontend starten       (nur Vite-Server)
#   - PI-Installer Frontend (App-Fenster) (Tauri-Fenster)
#   - PI-Installer Frontend (Browser)     (Vite + Standard-Browser)

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
START_SCRIPT="$PROJECT_ROOT/start-frontend-desktop.sh"

# Startskript ausführbar machen
chmod +x "$START_SCRIPT" 2>/dev/null
chmod +x "$PROJECT_ROOT/start-frontend.sh" 2>/dev/null

# Desktop-Ordner (englisch und/oder deutsch)
DESKTOPS=()
[ -d "$HOME/Desktop" ]      && DESKTOPS+=("$HOME/Desktop")
[ -d "$HOME/Schreibtisch" ] && DESKTOPS+=("$HOME/Schreibtisch")
[ ${#DESKTOPS[@]} -eq 0 ]   && DESKTOPS+=("$HOME")

for DESKTOP in "${DESKTOPS[@]}"; do
  LAUNCHER_DIR="$DESKTOP/PI-Installer"
  mkdir -p "$LAUNCHER_DIR"

  # 1) Nur Server (wie bisher)
  DESKTOP_FILE="$LAUNCHER_DIR/PI-Installer-Frontend-starten.desktop"
  cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=PI-Installer Frontend starten
Comment=Nur Vite-Server (Port 3001), Fenster/Browser manuell öffnen
Exec=$START_SCRIPT
Path=$PROJECT_ROOT
Icon=utilities-terminal
Terminal=true
Categories=Development;System;
EOF
  chmod +x "$DESKTOP_FILE"
  echo "✅ $DESKTOP_FILE"

  # 2) App-Fenster (Tauri)
  DESKTOP_FILE="$LAUNCHER_DIR/PI-Installer-Frontend-App-Fenster.desktop"
  cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=PI-Installer Frontend (App-Fenster)
Comment=Frontend im eigenen Fenster starten (Tauri)
Exec=$START_SCRIPT --window
Path=$PROJECT_ROOT
Icon=utilities-terminal
Terminal=true
Categories=Development;System;
EOF
  chmod +x "$DESKTOP_FILE"
  echo "✅ $DESKTOP_FILE"

  # 3) Browser
  DESKTOP_FILE="$LAUNCHER_DIR/PI-Installer-Frontend-Browser.desktop"
  cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=PI-Installer Frontend (Browser)
Comment=Frontend starten und im Standard-Browser öffnen
Exec=$START_SCRIPT --browser
Path=$PROJECT_ROOT
Icon=utilities-terminal
Terminal=true
Categories=Development;System;
EOF
  chmod +x "$DESKTOP_FILE"
  echo "✅ $DESKTOP_FILE"
done

echo ""
echo "Starter auf dem Desktop:"
echo "  • PI-Installer Frontend starten       → nur Vite-Server"
echo "  • PI-Installer Frontend (App-Fenster) → eigenes Fenster (Tauri)"
echo "  • PI-Installer Frontend (Browser)     → Vite + Standard-Browser"
