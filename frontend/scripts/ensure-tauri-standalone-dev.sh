#!/usr/bin/env bash
# Tauri Dev ohne Warten auf Backend (Development Cockpit Standalone-Modus).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$FRONTEND_DIR"
export SETUPHELFER_TAURI_STANDALONE=1
export PI_INSTALLER_TAURI_STANDALONE=1
export SETUPHELFER_SKIP_SERVICE_CONFLICT_GUARD=1
export PI_INSTALLER_SKIP_SERVICE_CONFLICT_GUARD=1
echo "Tauri Dev (Standalone): Backend optional — Cockpit nutzt Workspace-Fallback wenn API offline."
exec bash scripts/ensure-backend-then-dev.sh
