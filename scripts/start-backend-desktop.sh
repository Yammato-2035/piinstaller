#!/bin/bash
# PI-Installer Backend neu starten (für Desktop-Starter)
# Beendet laufendes Backend auf Port 8000 und startet es neu.

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo "🔄 PI-Installer Backend neu starten"
echo "===================================="

# Laufendes Backend auf Port 8000 beenden
if command -v lsof >/dev/null 2>&1; then
  PID=$(lsof -t -i:8000 2>/dev/null)
  if [ -n "$PID" ]; then
    echo "⏹  Beende bisheriges Backend (PID $PID)..."
    kill "$PID" 2>/dev/null
    sleep 2
    # Falls noch aktiv, hart beenden
    if lsof -t -i:8000 >/dev/null 2>&1; then
      kill -9 $(lsof -t -i:8000) 2>/dev/null
      sleep 1
    fi
  fi
fi

echo ""
exec "$PROJECT_ROOT/start-backend.sh"
