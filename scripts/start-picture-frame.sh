#!/bin/bash
# PI-Installer – Bilderrahmen (Fotos im Loop auf dem DSI/TFT-Display)
# Öffnet die PI-Installer-Oberfläche auf der TFT-Seite (Bilderrahmen-Modus).
# Startet das Frontend automatisch auf Port 3001, wenn es noch nicht läuft.
#
# Verwendung: ./scripts/start-picture-frame.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$REPO_ROOT/frontend"

# Port ermitteln: 5173 = Tauri-Dev, 3001 = normaler Vite-Server
detect_port() {
  if ss -tuln 2>/dev/null | grep -q ':5173 '; then
    echo "5173"
  elif ss -tuln 2>/dev/null | grep -qE ':3001 |:3002 '; then
    echo "3001"
  else
    echo "3001"
  fi
}

port_listening() {
  ss -tuln 2>/dev/null | grep -q ":$1 "
}

PORT=$(detect_port)

# Wenn weder 3001 noch 5173 laufen: Vite auf 3001 im Hintergrund starten
if ! port_listening 3001 && ! port_listening 5173; then
  echo "Frontend läuft nicht – starte Vite auf Port 3001 …"
  if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "📦 Installiere Dependencies …"
    (cd "$FRONTEND_DIR" && npm install) || { echo "Fehler: npm install fehlgeschlagen."; exit 1; }
  fi
  cd "$FRONTEND_DIR" || exit 1
  nohup npm run dev </dev/null >/dev/null 2>&1 &
  VITE_PID=$!
  disown $VITE_PID 2>/dev/null || true
  # Warten bis Port 3001 lauscht (max. 30 s)
  for i in $(seq 1 30); do
    sleep 1
    if port_listening 3001; then
      sleep 2
      break
    fi
    if ! kill -0 "$VITE_PID" 2>/dev/null; then
      echo "Vite konnte nicht gestartet werden."
      exit 1
    fi
  done
  if ! port_listening 3001; then
    echo "Timeout: Vite antwortet nicht auf Port 3001."
    kill "$VITE_PID" 2>/dev/null
    exit 1
  fi
  PORT="3001"
  echo "Frontend bereit."
fi

FRONTEND_URL="http://127.0.0.1:${PORT}/?page=tft"

BROWSER=""
for b in chromium chromium-browser chromium-wayland firefox firefox-esr midori epiphany; do
  if command -v "$b" >/dev/null 2>&1; then
    BROWSER="$b"
    break
  fi
done

if [ -z "$BROWSER" ]; then
  echo "Kein Browser gefunden. Bitte öffnen Sie: $FRONTEND_URL"
  exit 1
fi

echo "Öffne Bilderrahmen (TFT-Seite): $FRONTEND_URL"
exec xdg-open "$FRONTEND_URL" 2>/dev/null || exec "$BROWSER" "$FRONTEND_URL"
