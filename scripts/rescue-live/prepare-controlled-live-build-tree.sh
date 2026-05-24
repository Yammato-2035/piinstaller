#!/usr/bin/env bash
# Bereitet live-build-Arbeitsbaum unter build/rescue/live-build/ vor.
# Kein lb build, apt, chroot, mount, dd, mkfs, parted, /opt oder /etc write.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_ROOT="${REPO_ROOT}/build/rescue/live-build/setuphelfer-rescue-live"
BUNDLE_SRC="${REPO_ROOT}/build/rescue/temp-runtime/setuphelfer-rescue-runtime"
BUNDLE_DST="${BUILD_ROOT}/config/includes.chroot/opt/setuphelfer-rescue"
SOURCE_HEAD="$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"

die() { echo "ERROR: $*" >&2; exit 1; }

[[ -d "$BUNDLE_SRC" ]] || die "temp runtime bundle missing — run create-temp-runtime-bundle.sh first"
[[ -f "$BUNDLE_SRC/MANIFEST.json" ]] || die "bundle MANIFEST.json missing"

mkdir -p \
  "${BUILD_ROOT}/config/package-lists" \
  "${BUILD_ROOT}/config/includes.chroot/etc/systemd/system" \
  "${BUILD_ROOT}/config/includes.chroot/etc/systemd/network" \
  "${BUILD_ROOT}/config/hooks/normal" \
  "${BUILD_ROOT}/config/bootloaders" \
  "${BUILD_ROOT}/auto" \
  "${BUILD_ROOT}/evidence"

cat > "${BUILD_ROOT}/config/package-lists/setuphelfer.list.chroot" <<'EOF'
systemd
systemd-sysv
ca-certificates
curl
jq
iproute2
iputils-ping
net-tools
util-linux
lsblk
smartmontools
python3
python3-venv
python3-pip
EOF

cat > "${BUILD_ROOT}/config/includes.chroot/etc/systemd/network/20-wired.network" <<'EOF'
[Match]
Name=en*

[Network]
DHCP=yes
IPv6AcceptRA=yes
EOF

cat > "${BUILD_ROOT}/config/includes.chroot/etc/systemd/network/25-ethernet-alt.network" <<'EOF'
[Match]
Name=eth*

[Network]
DHCP=yes
IPv6AcceptRA=yes
EOF

cat > "${BUILD_ROOT}/config/includes.chroot/etc/systemd/system/setuphelfer-backend.service" <<'EOF'
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

cat > "${BUILD_ROOT}/config/includes.chroot/etc/systemd/system/setuphelfer.service" <<'EOF'
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

cat > "${BUILD_ROOT}/config/hooks/normal/010-enable-setuphelfer-services.hook.chroot" <<'EOF'
#!/bin/sh
set -eu
systemctl enable systemd-networkd.service || true
systemctl enable setuphelfer-backend.service || true
systemctl enable setuphelfer.service || true
EOF
chmod +x "${BUILD_ROOT}/config/hooks/normal/010-enable-setuphelfer-services.hook.chroot"

cat > "${BUILD_ROOT}/auto/config" <<'EOF'
#!/bin/sh
set -eu
lb config noauto \
  --distribution bookworm \
  --archive-areas "main" \
  --binary-images iso-hybrid \
  --debian-installer false \
  --bootappend-live "boot=live components quiet splash setuphelfer_rescue=1" \
  --iso-volume "SETUPHELFER_RESCUE" \
  --iso-application "Setuphelfer Rescue Live"
EOF
chmod +x "${BUILD_ROOT}/auto/config"

cat > "${BUILD_ROOT}/auto/build" <<'EOF'
#!/bin/sh
set -eu
echo "Use controlled gate before running lb build."
exit 20
EOF
chmod +x "${BUILD_ROOT}/auto/build"

cat > "${BUILD_ROOT}/auto/clean" <<'EOF'
#!/bin/sh
set -eu
lb clean
EOF
chmod +x "${BUILD_ROOT}/auto/clean"

rm -rf "$BUNDLE_DST"
mkdir -p "$(dirname "$BUNDLE_DST")"
rsync -aL \
  --exclude='__pycache__' --exclude='*.pyc' --exclude='.env' \
  --exclude='node_modules' --exclude='*.iso' --exclude='*.img' --exclude='*.qcow2' \
  "$BUNDLE_SRC/" "$BUNDLE_DST/"

MANIFEST_SHA="$(sha256sum "$BUNDLE_SRC/MANIFEST.json" | awk '{print $1}')"
BUNDLE_FILES="$(python3 - "$BUNDLE_SRC/MANIFEST.json" <<'PY'
import json, sys
print(json.loads(open(sys.argv[1]).read())["files_count"])
PY
)"

cat > "${BUILD_ROOT}/evidence/build-tree-manifest.json" <<EOF
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

cat > "${BUILD_ROOT}/README_SETUPHELFER_RESCUE_LIVE.md" <<EOF
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
