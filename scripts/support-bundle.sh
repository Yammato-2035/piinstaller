#!/usr/bin/env bash
# Support-Bundle erstellen: Logs, system_snapshot, debug.config.
# Aufruf: ./scripts/support-bundle.sh [output_dir]
# oder: cd backend && python -m debug.cli support-bundle [output_dir]

set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT/backend"
exec python3 -m debug.cli support-bundle "$@"
