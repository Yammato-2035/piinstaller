#!/bin/bash
# Startet das Setuphelfer-Backend als systemd-Service neu.

set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

_restart() {
  local u="$1"
  echo "🔄 Starte Backend-Service neu ($u)..."
  sudo systemctl restart "$u"
  sleep 1
  if systemctl is-active --quiet "$u"; then
    echo "✅ $u läuft."
    exit 0
  fi
  echo "❌ Service startet nicht. Log: sudo journalctl -u $u -n 30"
  exit 1
}

if systemctl list-unit-files --type=service 2>/dev/null | grep -q '^setuphelfer-backend.service'; then
  _restart setuphelfer-backend
fi
if systemctl list-unit-files --type=service 2>/dev/null | grep -q '^pi-installer-backend.service'; then
  _restart pi-installer-backend
fi

echo "ℹ️  Kein bekannter Backend-Service installiert."
echo "   Backend manuell: $REPO_ROOT/scripts/start-backend.sh"
echo "   Oder: ./scripts/install-backend-service.sh"
exit 0
