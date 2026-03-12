#!/bin/bash
# Startet das PI-Installer-Backend als systemd-Service neu.
# Nach Backend-Updates ausführen: ./scripts/restart-backend-service.sh
# Oder: sudo systemctl restart pi-installer-backend

set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if systemctl list-unit-files --type=service 2>/dev/null | grep -q '^pi-installer-backend.service'; then
  echo "🔄 Starte Backend-Service neu..."
  sudo systemctl restart pi-installer-backend
  sleep 1
  if systemctl is-active --quiet pi-installer-backend; then
    echo "✅ pi-installer-backend läuft."
  else
    echo "❌ Service startet nicht. Log: sudo journalctl -u pi-installer-backend -n 30"
    exit 1
  fi
else
  echo "ℹ️  Service pi-installer-backend nicht installiert."
  echo "   Backend manuell starten: $REPO_ROOT/scripts/start-backend.sh"
  echo "   Oder Service einrichten: ./scripts/create_installer.sh"
  exit 0
fi
