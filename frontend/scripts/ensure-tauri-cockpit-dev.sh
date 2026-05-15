#!/usr/bin/env bash
# Tauri Dev: Hauptfenster + externes Development Control Center (Live-Governance).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$FRONTEND_DIR"
export SETUPHELFER_OPEN_COCKPIT_ON_START=1
exec bash scripts/ensure-backend-then-dev.sh
