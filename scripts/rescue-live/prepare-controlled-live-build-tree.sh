#!/usr/bin/env bash
# Bereitet live-build-Arbeitsbaum unter build/rescue/live-build/ vor.
# Kein lb build, apt, chroot, mount, dd, mkfs, parted, /opt oder /etc write.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_ROOT="${REPO_ROOT}/build/rescue/live-build/setuphelfer-rescue-live"
BUNDLE_SRC="${REPO_ROOT}/build/rescue/temp-runtime/setuphelfer-rescue-runtime"
BUNDLE_DST="${BUILD_ROOT}/config/includes.chroot/opt/setuphelfer-rescue"
BOOTLOADER_DIR="${BUILD_ROOT}/config/bootloaders/isolinux"
BOOTLOADER_TEMPLATE_ROOT="/usr/share/live/build/bootloaders/isolinux"
TRASH_ROOT="${REPO_ROOT}/build/rescue/.trash"

git_workspace() {
  git -c "safe.directory=${REPO_ROOT}" -C "$REPO_ROOT" "$@"
}

write_text_file() {
  local target="$1"
  local mode="$2"
  local tmp
  mkdir -p "$(dirname "$target")"
  tmp="$(mktemp "${target}.tmp.XXXXXX")"
  cat > "$tmp"
  chmod "$mode" "$tmp"
  mv -f "$tmp" "$target"
}

copy_host_file() {
  local source="$1"
  local target="$2"
  local mode="$3"
  mkdir -p "$(dirname "$target")"
  install -m "$mode" "$source" "$target"
}

first_existing_file() {
  local candidate
  for candidate in "$@"; do
    if [[ -f "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

move_to_trash() {
  local source="$1"
  local target
  [[ -e "$source" ]] || return 0
  mkdir -p "$TRASH_ROOT"
  target="${TRASH_ROOT}/$(basename "$source").$(date +%s).$$"
  mv "$source" "$target"
}

SOURCE_HEAD="$(git_workspace rev-parse --short HEAD 2>/dev/null || echo unknown)"

die() { echo "ERROR: $*" >&2; exit 1; }

[[ -d "$BUNDLE_SRC" ]] || die "temp runtime bundle missing — run create-temp-runtime-bundle.sh first"
[[ -f "$BUNDLE_SRC/MANIFEST.json" ]] || die "bundle MANIFEST.json missing"

mkdir -p \
  "${BUILD_ROOT}/config/package-lists" \
  "${BUILD_ROOT}/config/archives" \
  "${BUILD_ROOT}/config/includes.chroot/etc/systemd/system" \
  "${BUILD_ROOT}/config/includes.chroot/etc/systemd/network" \
  "${BUILD_ROOT}/config/hooks/normal" \
  "${BOOTLOADER_DIR}" \
  "${BUILD_ROOT}/auto" \
  "${BUILD_ROOT}/evidence"

HOST_ISOLINUX_BIN="$(first_existing_file /usr/lib/ISOLINUX/isolinux.bin /usr/lib/syslinux/isolinux.bin || true)"
HOST_VESAMENU_C32="$(first_existing_file /usr/lib/syslinux/modules/bios/vesamenu.c32 /usr/lib/syslinux/vesamenu.c32 || true)"
[[ -f "${BOOTLOADER_TEMPLATE_ROOT}/install.cfg" ]] || die "live-build isolinux template missing: ${BOOTLOADER_TEMPLATE_ROOT}"
[[ -n "$HOST_ISOLINUX_BIN" ]] || die "host isolinux.bin missing — install package isolinux"
[[ -n "$HOST_VESAMENU_C32" ]] || die "host vesamenu.c32 missing — install package syslinux-common"

copy_host_file "${BOOTLOADER_TEMPLATE_ROOT}/install.cfg" "${BOOTLOADER_DIR}/install.cfg" 0644
copy_host_file "${BOOTLOADER_TEMPLATE_ROOT}/isolinux.cfg" "${BOOTLOADER_DIR}/isolinux.cfg" 0644
copy_host_file "${BOOTLOADER_TEMPLATE_ROOT}/live.cfg.in" "${BOOTLOADER_DIR}/live.cfg.in" 0644
copy_host_file "${BOOTLOADER_TEMPLATE_ROOT}/menu.cfg" "${BOOTLOADER_DIR}/menu.cfg" 0644
copy_host_file "${BOOTLOADER_TEMPLATE_ROOT}/splash.svg.in" "${BOOTLOADER_DIR}/splash.svg.in" 0644
copy_host_file "${BOOTLOADER_TEMPLATE_ROOT}/stdmenu.cfg" "${BOOTLOADER_DIR}/stdmenu.cfg" 0644
copy_host_file "$HOST_ISOLINUX_BIN" "${BOOTLOADER_DIR}/isolinux.bin" 0644
copy_host_file "$HOST_VESAMENU_C32" "${BOOTLOADER_DIR}/vesamenu.c32" 0644
for module in ldlinux.c32 libcom32.c32 libutil.c32 libmenu.c32; do
  module_path="$(first_existing_file "/usr/lib/syslinux/modules/bios/${module}" "/usr/lib/syslinux/${module}" || true)"
  if [[ -n "$module_path" ]]; then
    copy_host_file "$module_path" "${BOOTLOADER_DIR}/${module}" 0644
  fi
done

write_text_file "${BUILD_ROOT}/config/package-lists/setuphelfer.list.chroot" 0644 <<'EOF'
systemd
systemd-sysv
ca-certificates
curl
jq
iproute2
iputils-ping
net-tools
util-linux
smartmontools
python3
python3-venv
python3-pip
EOF

write_text_file "${BUILD_ROOT}/config/includes.chroot/etc/systemd/network/20-wired.network" 0644 <<'EOF'
[Match]
Name=en*

[Network]
DHCP=yes
IPv6AcceptRA=yes
EOF

write_text_file "${BUILD_ROOT}/config/includes.chroot/etc/systemd/network/25-ethernet-alt.network" 0644 <<'EOF'
[Match]
Name=eth*

[Network]
DHCP=yes
IPv6AcceptRA=yes
EOF

write_text_file "${BUILD_ROOT}/config/archives/debian-security.list.chroot" 0644 <<'EOF'
deb http://security.debian.org/ bookworm-security main
EOF

write_text_file "${BUILD_ROOT}/config/archives/debian-security.list.binary" 0644 <<'EOF'
deb http://security.debian.org/ bookworm-security main
EOF

write_text_file "${BUILD_ROOT}/config/includes.chroot/etc/systemd/system/setuphelfer-backend.service" 0644 <<'EOF'
[Unit]
Description=Setuphelfer Rescue Backend
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/setuphelfer-rescue
Environment=SETUPHELFER_RESCUE_ROOT=/opt/setuphelfer-rescue
Environment=SETUPHELFER_RESCUE_MODE=1
Environment=SETUPHELFER_DISABLE_WRITES=1
ExecStart=/opt/setuphelfer-rescue/scripts/rescue-live/start-backend-localonly.sh
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/tmp /run /var/tmp

[Install]
WantedBy=multi-user.target
EOF

write_text_file "${BUILD_ROOT}/config/includes.chroot/etc/systemd/system/setuphelfer.service" 0644 <<'EOF'
[Unit]
Description=Setuphelfer Rescue Web UI
After=setuphelfer-backend.service
Wants=setuphelfer-backend.service

[Service]
Type=simple
WorkingDirectory=/opt/setuphelfer-rescue
Environment=SETUPHELFER_RESCUE_ROOT=/opt/setuphelfer-rescue
Environment=SETUPHELFER_RESCUE_MODE=1
Environment=SETUPHELFER_DISABLE_WRITES=1
ExecStart=/opt/setuphelfer-rescue/scripts/rescue-live/start-ui-localonly.sh
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/tmp /run /var/tmp

[Install]
WantedBy=multi-user.target
EOF

write_text_file "${BUILD_ROOT}/config/hooks/normal/010-enable-setuphelfer-services.hook.chroot" 0755 <<'EOF'
#!/bin/sh
set -eu
systemctl enable systemd-networkd.service || true
systemctl enable setuphelfer-backend.service || true
systemctl enable setuphelfer.service || true
EOF

write_text_file "${BUILD_ROOT}/auto/config" 0755 <<'EOF'
#!/bin/sh
set -eu
lb config noauto \
  --distribution bookworm \
  --archive-areas "main" \
  --binary-images iso-hybrid \
  --debian-installer false \
  --security false \
  --firmware-chroot false \
  --firmware-binary false \
  --bootappend-live "boot=live components quiet splash setuphelfer_rescue=1" \
  --iso-volume "SETUPHELFER_RESCUE" \
  --iso-application "Setuphelfer Rescue Live"
EOF

write_text_file "${BUILD_ROOT}/auto/build" 0755 <<'EOF'
#!/bin/sh
set -eu
echo "Use controlled gate before running lb build."
exit 20
EOF

write_text_file "${BUILD_ROOT}/auto/clean" 0755 <<'EOF'
#!/bin/sh
set -eu
# Kein "lb clean" hier: live-build ruft auto/clean selbst auf und wuerde sonst rekursiv enden.
rm -rf .build chroot cache binary local
EOF

if [[ -e "$BUNDLE_DST" ]]; then
  move_to_trash "$BUNDLE_DST"
fi
for stale_bundle in "$(dirname "$BUNDLE_DST")/$(basename "$BUNDLE_DST").old."*; do
  [[ -e "$stale_bundle" ]] || continue
  move_to_trash "$stale_bundle"
done
mkdir -p "$(dirname "$BUNDLE_DST")"
rsync -rltL \
  --exclude='__pycache__' --exclude='*.pyc' --exclude='.env' \
  --exclude='node_modules' --exclude='*.iso' --exclude='*.img' --exclude='*.qcow2' \
  "$BUNDLE_SRC/" "$BUNDLE_DST/"

MANIFEST_SHA="$(sha256sum "$BUNDLE_SRC/MANIFEST.json" | awk '{print $1}')"
BUNDLE_FILES="$(python3 - "$BUNDLE_SRC/MANIFEST.json" <<'PY'
import json, sys
print(json.loads(open(sys.argv[1]).read())["files_count"])
PY
)"

write_text_file "${BUILD_ROOT}/evidence/build-tree-manifest.json" 0644 <<EOF
{
  "controlled_live_build_tree": true,
  "no_real_build_execution": true,
  "source_head": "${SOURCE_HEAD}",
  "bundle_source": "build/rescue/temp-runtime/setuphelfer-rescue-runtime",
  "bundle_files_count": ${BUNDLE_FILES},
  "bundle_manifest_sha256": "${MANIFEST_SHA}",
  "real_iso_build_allowed": false,
  "usb_write_allowed": false
}
EOF

write_text_file "${BUILD_ROOT}/README_SETUPHELFER_RESCUE_LIVE.md" 0644 <<EOF
# Setuphelfer Rescue Live — Controlled Build Tree

- Source HEAD: ${SOURCE_HEAD}
- Bundle MANIFEST sha256: ${MANIFEST_SHA}
- **real_iso_build_allowed:** false
- **usb_write_allowed:** false

## Vorbereitung (bereits erledigt durch prepare-controlled-live-build-tree.sh)

1. Temp-Runtime-Bundle unter \`config/includes.chroot/opt/setuphelfer-rescue/\`
2. Paketliste, systemd-networkd, local-only Services, Hooks

## ISO-Build (NUR nach Operator-Freigabe)

\`\`\`bash
cd build/rescue/live-build/setuphelfer-rescue-live
./auto/config
# NICHT automatisch:
# lb build
\`\`\`

Siehe \`docs/runbooks/RESCUE_CONTROLLED_ISO_BUILD_RUNBOOK.md\`.
EOF

echo "OK: controlled live build tree at ${BUILD_ROOT}"
echo "OK: bundle copied to includes.chroot/opt/setuphelfer-rescue (${BUNDLE_FILES} files ref)"
