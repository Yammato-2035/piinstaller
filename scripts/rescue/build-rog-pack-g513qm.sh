#!/usr/bin/env bash
# build-rog-pack-g513qm.sh — download slim offline nvidia debs, write MANIFEST, optional stick copy.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PACK_SRC="${REPO_ROOT}/scripts/rescue/rog-pack-g513qm"
NVIDIA_METAPKG="${NVIDIA_METAPKG:-nvidia-driver-550}"
COPY_TO_STICK=0
STICK_LOGS=""
DRY_RUN=0

usage() {
  cat <<EOF
Usage: $(basename "$0") [--copy-to-stick PATH_TO_SETUP_LOGS] [--nvidia PKG] [--dry-run]

Slim offline pack (apt --download-only, no recommends). Avoids pulling every
linux-modules-nvidia-* cloud kernel variant.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --copy-to-stick) COPY_TO_STICK=1; STICK_LOGS="${2:-}"; shift ;;
    --nvidia) NVIDIA_METAPKG="${2:-}"; shift ;;
    --dry-run) DRY_RUN=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown: $1" >&2; usage; exit 2 ;;
  esac
  shift
done

mkdir -p "$PACK_SRC/debs/nvidia" "$PACK_SRC/debs/firmware" \
  "$PACK_SRC/config/modprobe.d" "$PACK_SRC/config/grub-profiles" "$PACK_SRC/scripts"
chmod +x "$PACK_SRC/scripts/"*.sh 2>/dev/null || true

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "DRY: would apt-get update && download-only $NVIDIA_METAPKG dkms"
else
  sudo apt-get update -qq
  CACHE="$(mktemp -d /tmp/rog-nvidia-cache.XXXXXX)"
  mkdir -p "$CACHE/archives/partial"
  # shellcheck disable=SC2086
  sudo apt-get install -y --download-only -o Dir::Cache="$CACHE" \
    -o APT::Install-Recommends=false \
    "$NVIDIA_METAPKG" dkms
  rm -f "$PACK_SRC"/debs/nvidia/*.deb
  # archives owned by root
  sudo cp -a "$CACHE"/archives/*.deb "$PACK_SRC/debs/nvidia/"
  sudo chown "$(id -u):$(id -g)" "$PACK_SRC"/debs/nvidia/*.deb
  sudo rm -rf "$CACHE"
  (
    cd "$PACK_SRC/debs/nvidia"
    apt-get download dkms || true
  )
fi

UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
if [[ "$DRY_RUN" -eq 0 ]]; then
  python3 - <<PY
import hashlib, json
from pathlib import Path
root = Path(r"$PACK_SRC")
files = []
for p in sorted(root.rglob("*")):
    if p.is_file() and p.name != "MANIFEST.json":
        files.append({
            "path": str(p.relative_to(root)),
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "bytes": p.stat().st_size,
        })
doc = {
    "pack_id": "g513qm",
    "contract": "rog-pack-g513qm-v1",
    "created_utc": "$UTC",
    "mint_version": "22.2",
    "ubuntu_base": "24.04",
    "live_kernel_hint": "6.14.0-29-generic",
    "nvidia_metapackage": "$NVIDIA_METAPKG",
    "pack_note": "Slim apt --download-only; no cloud kernel image noise",
    "files": files,
}
(root / "MANIFEST.json").write_text(json.dumps(doc, indent=2) + "\n")
print("Wrote MANIFEST files", len(files))
PY
fi

if [[ "$COPY_TO_STICK" -eq 1 ]]; then
  [[ -n "$STICK_LOGS" && -d "$STICK_LOGS" ]] || {
    echo "SETUP_LOGS path missing: $STICK_LOGS" >&2
    exit 5
  }
  DEST="$STICK_LOGS/setuphelfer/rog-pack/g513qm"
  echo "Copying pack to $DEST ..."
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "DRY: rsync to $DEST"
  else
    mkdir -p "$DEST"
    rsync -a --delete "$PACK_SRC"/ "$DEST"/
    sync
    echo "Stick pack ready: $DEST"
  fi
fi

echo "Done. Pack source: $PACK_SRC"
du -sh "$PACK_SRC/debs/nvidia" || true
