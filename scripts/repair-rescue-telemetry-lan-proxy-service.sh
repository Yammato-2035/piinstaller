#!/bin/bash
# Re-render and restart setuphelfer-rescue-telemetry-lan-proxy.service (fixes {{INSTALL_DIR}} drift).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
exec "$SCRIPT_DIR/install-rescue-telemetry-lan-proxy-service.sh"
