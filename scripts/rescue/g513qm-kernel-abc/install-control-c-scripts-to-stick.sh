#!/usr/bin/env bash
# Copy Control-C diagnostic scripts onto SETUP_LOGS pack (no NVMe, no remaster).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
LOGS_MNT="${1:-}"
if [[ -z "$LOGS_MNT" ]]; then
  echo "Usage: $0 /mount/SETUP_LOGS" >&2
  exit 2
fi
# Identity gate
UUID="$(findmnt -no UUID "$LOGS_MNT" 2>/dev/null || true)"
LABEL="$(findmnt -no LABEL "$LOGS_MNT" 2>/dev/null || true)"
if [[ "$UUID" != "9BC7-3950" && "$LABEL" != "SETUP_LOGS" && "$LABEL" != "SETUP_LOGS2" ]]; then
  echo "BLOCKED: carrier_identity_gate failed uuid=$UUID label=$LABEL" >&2
  exit 20
fi
DEST="$LOGS_MNT/setuphelfer/rog-pack/g513qm"
mkdir -p "$DEST/scripts" "$DEST/systemd" "$DEST/config"
cp -a "$ROOT/scripts/rescue/rog-pack-g513qm/scripts/setuphelfer-gpu" "$DEST/scripts/"
cp -a "$ROOT/scripts/rescue/rog-pack-g513qm/scripts/setuphelfer-early-capture.sh" "$DEST/scripts/"
cp -a "$ROOT/scripts/rescue/rog-pack-g513qm/scripts/setuphelfer-netconsole-config.sh" "$DEST/scripts/"
cp -a "$ROOT/scripts/rescue/rog-pack-g513qm/systemd/"*.service "$DEST/systemd/"
cp -a "$ROOT/config/rescue/g513qm_graphics_profiles.json" "$DEST/config/"
cp -a "$ROOT/config/rescue/g513qm_netconsole_lab.json" "$DEST/config/"
chmod +x "$DEST/scripts/setuphelfer-gpu" \
  "$DEST/scripts/setuphelfer-early-capture.sh" \
  "$DEST/scripts/setuphelfer-netconsole-config.sh"
echo "Installed Control-C scripts to $DEST"
echo "NOTE: systemd units require remaster OR manual copy into live root for auto-start."
echo "With systemd.debug-shell=1 use Ctrl+Alt+F9 and run scripts from this pack path."
