#!/usr/bin/env bash
# apply-rog-pack.sh — install G513QM offline pack into running or chrooted Mint system.
set -euo pipefail

PACK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DRY_RUN=0
CHROOT=""
SKIP_NVIDIA=0
PHRASE_OK=0

usage() {
  cat <<EOF
Usage: $(basename "$0") [--dry-run] [--chroot DIR] [--skip-nvidia] [--i-understand-no-windows-wipe]

Installs modprobe configs and offline NVIDIA debs from:
  $PACK_ROOT

Does not wipe disks. Windows/BitLocker must remain untouched by the operator.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --chroot) CHROOT="${2:-}"; shift ;;
    --skip-nvidia) SKIP_NVIDIA=1 ;;
    --i-understand-no-windows-wipe) PHRASE_OK=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 2 ;;
  esac
  shift
done

if [[ "$PHRASE_OK" -ne 1 ]]; then
  echo "Refusing: pass --i-understand-no-windows-wipe (this script never wipes, but confirms operator policy)." >&2
  exit 3
fi

run() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "DRY: $*"
  else
    "$@"
  fi
}

root_path() {
  local p="$1"
  if [[ -n "$CHROOT" ]]; then
    echo "${CHROOT}${p}"
  else
    echo "$p"
  fi
}

echo "PACK_ROOT=$PACK_ROOT"
[[ -f "$PACK_ROOT/MANIFEST.json" ]] || echo "WARN: MANIFEST.json missing (run build-rog-pack-g513qm.sh)"

# --- modprobe configs ---
MOD_DST="$(root_path /etc/modprobe.d)"
run mkdir -p "$MOD_DST"
for f in "$PACK_ROOT"/config/modprobe.d/*.conf; do
  [[ -f "$f" ]] || continue
  base="$(basename "$f")"
  # Install nvidia-drm.conf only when not skipping nvidia
  if [[ "$base" == "nvidia-drm.conf" && "$SKIP_NVIDIA" -eq 1 ]]; then
    continue
  fi
  run cp -a "$f" "$MOD_DST/$base"
  echo "Installed modprobe: $base"
done

# --- nvidia debs ---
if [[ "$SKIP_NVIDIA" -eq 0 ]]; then
  mapfile -t DEBS < <(find "$PACK_ROOT/debs/nvidia" -maxdepth 1 -name '*.deb' | sort)
  if [[ "${#DEBS[@]}" -eq 0 ]]; then
    echo "ERROR: no .deb in debs/nvidia — run build-rog-pack-g513qm.sh first" >&2
    exit 4
  fi
  if [[ -n "$CHROOT" ]]; then
    run mkdir -p "$CHROOT/tmp/rog-nvidia-debs"
    run cp -a "${DEBS[@]}" "$CHROOT/tmp/rog-nvidia-debs/"
    if [[ "$DRY_RUN" -eq 1 ]]; then
      echo "DRY: chroot $CHROOT dpkg -i /tmp/rog-nvidia-debs/*.deb"
    else
      chroot "$CHROOT" bash -c 'dpkg -i /tmp/rog-nvidia-debs/*.deb || apt-get -f install -y'
    fi
  else
    if [[ "$DRY_RUN" -eq 1 ]]; then
      echo "DRY: dpkg -i ${DEBS[*]}"
    else
      dpkg -i "${DEBS[@]}" || apt-get -f install -y
    fi
  fi
fi

# --- optional firmware debs ---
mapfile -t FW < <(find "$PACK_ROOT/debs/firmware" -maxdepth 1 -name '*.deb' 2>/dev/null | sort || true)
if [[ "${#FW[@]}" -gt 0 ]]; then
  if [[ -n "$CHROOT" ]]; then
    run mkdir -p "$CHROOT/tmp/rog-fw-debs"
    run cp -a "${FW[@]}" "$CHROOT/tmp/rog-fw-debs/"
    if [[ "$DRY_RUN" -eq 0 ]]; then
      chroot "$CHROOT" bash -c 'dpkg -i /tmp/rog-fw-debs/*.deb || apt-get -f install -y'
    fi
  else
    [[ "$DRY_RUN" -eq 1 ]] || dpkg -i "${FW[@]}" || apt-get -f install -y
  fi
fi

# --- drop grub profile snippets for operator ---
PROF_DST="$(root_path /usr/share/setuphelfer/rog-pack/grub-profiles)"
run mkdir -p "$PROF_DST"
run cp -a "$PACK_ROOT"/config/grub-profiles/*.txt "$PROF_DST/" 2>/dev/null || true

# --- mark first-boot done marker path ---
MARKER="$(root_path /var/lib/setuphelfer/rog-pack-applied)"
run mkdir -p "$(dirname "$MARKER")"
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "DRY: touch $MARKER"
else
  date -u +%Y-%m-%dT%H:%M:%SZ >"$MARKER"
  echo "kernel=$(uname -r)" >>"$MARKER" 2>/dev/null || true
fi

echo "apply-rog-pack finished (dry_run=$DRY_RUN chroot=${CHROOT:-none})"
echo "Next: update GRUB with config/grub-profiles/postinstall-amd-igpu.txt then reboot."
