#!/usr/bin/env bash
# PI-Installer – Test: Zeigt auf jedem Bildschirm den Ausgabe-Namen (z. B. DSI-1, HDMI-A-1).
# Hilft, den richtigen Namen für ensure-dsi-window-rule.sh (PI_INSTALLER_DSI_OUTPUT) zu finden.
#
# Start: ./scripts/display-names-test.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

if [ -d "apps/dsi_radio/.venv" ] && [ -f "apps/dsi_radio/.venv/bin/python" ]; then
  exec "apps/dsi_radio/.venv/bin/python" "$SCRIPT_DIR/display-names-test.py" "$@"
fi
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$SCRIPT_DIR/display-names-test.py" "$@"
fi
echo "python3 nicht gefunden."
exit 1
