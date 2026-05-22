#!/bin/bash
# Setuphelfer – Partitionshelfer (tkinter, Phase 1: Anzeige & Sicherheitsanalyse)
#
# Verwendung:
#   ./scripts/start-partitionshelfer.sh
#
# Voraussetzung: python3-tk, lsblk (siehe apps/partitionshelfer/install.sh)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_DIR="$REPO_ROOT/apps/partitionshelfer"

if [ ! -f "$APP_DIR/start.py" ]; then
  echo "Fehler: $APP_DIR/start.py nicht gefunden."
  exit 1
fi

exec python3 "$APP_DIR/start.py" "$@"
