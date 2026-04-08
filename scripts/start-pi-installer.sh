#!/bin/bash
# Legacy-Name: leitet auf den aktuellen Setuphelfer-Starter weiter.
# Bevorzugt: scripts/start-setuphelfer.sh
exec "$(cd "$(dirname "$0")" && pwd)/start-setuphelfer.sh" "$@"
