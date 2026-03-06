#!/usr/bin/env bash
# Support-Bundle erstellen: Logs, system_snapshot, debug.config.
# Aufruf: ./scripts/support-bundle.sh [output_dir]
#         ./scripts/support-bundle.sh --out-dir /tmp --max-log-lines 1000
# Exit: 0 = Erfolg, 1 = Fehler (CLI gibt Pfad aus bei Erfolg)

set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT/backend"
exec python3 -m debug.cli support-bundle "$@"
