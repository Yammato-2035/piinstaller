#!/usr/bin/env bash
# Stage graphical rescue assets into build tree overlay + asset manifest (no ISO build).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ASSETS_SRC="${REPO_ROOT}/assets/rescue"
BUILD_ROOT="${REPO_ROOT}/build/rescue/live-build/setuphelfer-rescue-live"
MANIFEST_OUT="${REPO_ROOT}/build/rescue/asset-manifest.json"
THEME_DIR="${REPO_ROOT}/build/rescue/theme/grub/setuphelfer"

die() { echo "ERROR: $*" >&2; exit "${2:-1}"; }

[[ -d "$ASSETS_SRC" ]] || die "assets/rescue missing" 22

stage_one() {
  local rel="$1"
  local src="${ASSETS_SRC}/${rel}"
  [[ -f "$src" ]] || die "missing asset: ${rel}" 23
  local share_dst="${BUILD_ROOT}/config/includes.chroot/usr/share/setuphelfer/rescue/assets/${rel}"
  local opt_dst="${BUILD_ROOT}/config/includes.chroot/opt/setuphelfer-rescue/assets/${rel}"
  mkdir -p "$(dirname "$share_dst")" "$(dirname "$opt_dst")"
  install -m 0644 "$src" "$share_dst"
  install -m 0644 "$src" "$opt_dst"
}

for rel in \
  logo/setuphelfer-logo2.png \
  boot-menu/setuphelfer-boot-menu-de.png \
  boot-menu/setuphelfer-boot-menu-en.png \
  splash/setuphelfer-splash.png \
  icons/setuphelfer-icon.png; do
  stage_one "$rel"
done

mkdir -p "$THEME_DIR"
install -m 0644 "${ASSETS_SRC}/boot-menu/setuphelfer-boot-menu-de.png" "${THEME_DIR}/setuphelfer-boot-menu-de.png"
if [[ ! -f "${THEME_DIR}/theme.txt" ]]; then
  cat >"${THEME_DIR}/theme.txt" <<'EOF'
# Setuphelfer GRUB theme — background/branding only; menu entries remain in grub.cfg
desktop-image: "setuphelfer-boot-menu-de.png"
title-text: "Setuphelfer Rettung"
title-color: "#ffffff"
message-color: "#e2e8f0"
EOF
fi
GRUB_THEME_DST="${BUILD_ROOT}/config/includes.binary/boot/grub/themes/setuphelfer"
mkdir -p "$GRUB_THEME_DST"
install -m 0644 "${THEME_DIR}/theme.txt" "${GRUB_THEME_DST}/theme.txt"
install -m 0644 "${ASSETS_SRC}/boot-menu/setuphelfer-boot-menu-de.png" "${GRUB_THEME_DST}/setuphelfer-boot-menu-de.png"

if [[ -d "${REPO_ROOT}/build/rescue/ui" ]]; then
  mkdir -p "${BUILD_ROOT}/config/includes.chroot/usr/share/setuphelfer/rescue/ui"
  cp -a "${REPO_ROOT}/build/rescue/ui/." "${BUILD_ROOT}/config/includes.chroot/usr/share/setuphelfer/rescue/ui/"
fi

for loc in de en; do
  src="${REPO_ROOT}/frontend/src/rescue/i18n/${loc}.json"
  if [[ -f "$src" ]]; then
    dst="${BUILD_ROOT}/config/includes.chroot/opt/setuphelfer-rescue/i18n/${loc}.json"
    mkdir -p "$(dirname "$dst")"
    install -m 0644 "$src" "$dst"
  fi
done

export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"
python3 - <<PY
import json
from pathlib import Path
from rescue.rescue_graphical_assets import build_asset_manifest

repo = Path(${REPO_ROOT@Q})
manifest = build_asset_manifest(repo)
manifest["staged_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
manifest["build_root"] = str(Path(${BUILD_ROOT@Q}))
out = Path(${MANIFEST_OUT@Q})
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(manifest, indent=2) + "\\n", encoding="utf-8")
print(json.dumps({"complete": manifest["complete"], "entries": len(manifest["entries"])}))
PY

echo "OK: graphical assets staged — manifest: ${MANIFEST_OUT}"
