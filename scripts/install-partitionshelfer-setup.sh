#!/bin/bash
# Setuphelfer – Partitionshelfer: Systemabhängigkeiten (python3-tk, lsblk)
#
# Verwendung (aus Projektroot):
#   sudo bash ./scripts/install-partitionshelfer-setup.sh
#
# Optional danach Desktop-Eintrag:
#   bash apps/partitionshelfer/install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_DIR="$REPO_ROOT/apps/partitionshelfer"

if [ ! -f "$APP_DIR/install.sh" ]; then
  echo "Fehler: $APP_DIR/install.sh nicht gefunden."
  exit 1
fi

bash "$APP_DIR/install.sh"
