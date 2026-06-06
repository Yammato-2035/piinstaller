#!/usr/bin/env bash
# Benennt Tauri-Bundle-Artefakte auf setuphelfer_project_version um (X.Y.Z.W).
# Tauri erzeugt nativ nur semver (X.Y.Z) in Dateinamen — das ist kein Versions-Drift.
#
# Projektversion ausschließlich aus config/version.json (Source of Truth).
#
# Verwendung (nach npm run tauri:build):
#   ./scripts/rename-tauri-bundle-artifacts.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUNDLE="$REPO_ROOT/frontend/src-tauri/target/release/bundle"
VERSION_JSON="$REPO_ROOT/config/version.json"

if [[ ! -d "$BUNDLE" ]]; then
  echo "rename-tauri-bundle-artifacts: bundle dir missing: $BUNDLE" >&2
  exit 1
fi

if [[ ! -f "$VERSION_JSON" ]]; then
  echo "rename-tauri-bundle-artifacts: missing $VERSION_JSON" >&2
  exit 1
fi

read -r PROJECT_VERSION SEMVER <<<"$(python3 - <<'PY' "$VERSION_JSON"
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))
pv = str(data.get("project_version") or "").strip()
if not pv:
    raise SystemExit("project_version missing")
parts = pv.split(".")
semver = ".".join(parts[:3]) if len(parts) >= 3 else pv
print(pv, semver)
PY
)"

PRODUCT="SetupHelfer"
renamed=0

rename_if_exists() {
  local dir="$1"
  local from="$2"
  local to="$3"
  if [[ -f "$dir/$from" && "$from" != "$to" ]]; then
    mv "$dir/$from" "$dir/$to"
    echo "rename-tauri-bundle-artifacts: $from -> $to"
    renamed=$((renamed + 1))
  fi
}

rename_if_exists "$BUNDLE/deb" "${PRODUCT}_${SEMVER}_amd64.deb" "${PRODUCT}_${PROJECT_VERSION}_amd64.deb"
rename_if_exists "$BUNDLE/rpm" "${PRODUCT}-${SEMVER}-1.x86_64.rpm" "${PRODUCT}-${PROJECT_VERSION}-1.x86_64.rpm"
rename_if_exists "$BUNDLE/appimage" "${PRODUCT}_${SEMVER}_amd64.AppImage" "${PRODUCT}_${PROJECT_VERSION}_amd64.AppImage"

echo "rename-tauri-bundle-artifacts: project_version=$PROJECT_VERSION semver=$SEMVER renamed=$renamed"
