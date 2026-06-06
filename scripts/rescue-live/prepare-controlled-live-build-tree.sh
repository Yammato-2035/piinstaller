#!/usr/bin/env bash
# Bereitet live-build-Arbeitsbaum unter build/rescue/live-build/ vor.
# Kein lb build, apt, chroot, mount, dd, mkfs, parted, /opt oder /etc write.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_ROOT="${REPO_ROOT}/build/rescue/live-build/setuphelfer-rescue-live"
RESCUE_BUILD_PROFILE="${SETUPHELFER_RESCUE_BUILD_PROFILE:-standard}"
DEV_PROFILE_ROOT="${REPO_ROOT}/build/rescue/profiles/developer"
BUNDLE_SRC="${REPO_ROOT}/build/rescue/temp-runtime/setuphelfer-rescue-runtime"
BUNDLE_DST="${BUILD_ROOT}/config/includes.chroot/opt/setuphelfer-rescue"
RSVG_COMPAT="${REPO_ROOT}/build/rescue/tool-compat/bin/rsvg"
RSVG_CHROOT="${BUILD_ROOT}/config/includes.chroot/usr/local/bin/rsvg"
BOOTLOADER_DIR="${BUILD_ROOT}/config/bootloaders/isolinux"
BOOTLOADER_TEMPLATE_ROOT="/usr/share/live/build/bootloaders/isolinux"
GRUB_EFI_DIR="${BUILD_ROOT}/config/bootloaders/grub-efi"
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

# lb_binary_syslinux always unpacks ${_TARGET}/bootlogo via cpio (Debian live-build theme
# ships splash.svg.in only). Without this seed archive, lb exits 2 after rsvg succeeds.
create_minimal_bootlogo_cpio() {
  local target="$1"
  local tmp
  tmp="$(mktemp -d)"
  printf '%s\n' 'gfxboot seed for Setuphelfer controlled ISO build' > "${tmp}/.gfxboot-seed"
  (cd "$tmp" && find . -print0 | cpio -o --null --quiet) > "${target}.tmp"
  mv -f "${target}.tmp" "$target"
  rm -rf "$tmp"
}

SOURCE_HEAD="$(git_workspace rev-parse --short HEAD 2>/dev/null || echo unknown)"

die() { echo "ERROR: $*" >&2; exit 1; }

[[ -d "$BUNDLE_SRC" ]] || die "temp runtime bundle missing — run create-temp-runtime-bundle.sh first"
[[ -f "$BUNDLE_SRC/MANIFEST.json" ]] || die "bundle MANIFEST.json missing"
[[ -x "$RSVG_COMPAT" ]] || die "rsvg compat wrapper missing: $RSVG_COMPAT"

mkdir -p \
  "${BUILD_ROOT}/config/package-lists" \
  "${BUILD_ROOT}/config/archives" \
  "${BUILD_ROOT}/config/includes.chroot/etc/systemd/system" \
  "${BUILD_ROOT}/config/includes.chroot/etc/systemd/network" \
  "${BUILD_ROOT}/config/includes.chroot/usr/local/bin" \
  "${BUILD_ROOT}/config/hooks/normal" \
  "${BOOTLOADER_DIR}" \
  "${GRUB_EFI_DIR}" \
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
copy_host_file "$RSVG_COMPAT" "$RSVG_CHROOT" 0755

copy_host_file "$HOST_ISOLINUX_BIN" "${BOOTLOADER_DIR}/isolinux.bin" 0644
copy_host_file "$HOST_VESAMENU_C32" "${BOOTLOADER_DIR}/vesamenu.c32" 0644
for module in ldlinux.c32 libcom32.c32 libutil.c32 libmenu.c32; do
  module_path="$(first_existing_file "/usr/lib/syslinux/modules/bios/${module}" "/usr/lib/syslinux/${module}" || true)"
  if [[ -n "$module_path" ]]; then
    copy_host_file "$module_path" "${BOOTLOADER_DIR}/${module}" 0644
  fi
done

create_minimal_bootlogo_cpio "${BOOTLOADER_DIR}/bootlogo"

write_text_file "${GRUB_EFI_DIR}/setuphelfer-grub-efi-note.txt" 0644 <<'EOF'
# Setuphelfer Rescue — UEFI-x64 boot (grub-efi-amd64)
#
# live-build >= bookworm: auto/config sets --bootloaders syslinux,grub-efi when supported.
# live-build 3.0 (Ubuntu): no grub-efi stage — operator runs after lb build:
#   scripts/rescue-live/patch-rescue-iso-uefi-x64.sh --in-place binary.hybrid.iso
#   scripts/rescue-live/validate-rescue-iso-uefi-boot.sh binary.hybrid.iso
#
# Required ISO markers after successful UEFI enablement:
#   /EFI/BOOT/BOOTX64.EFI
#   xorriso -report_el_torito shows EFI alt-boot (boot/grub/efi.img)
# init=/lib/systemd/systemd remains in --bootappend-live and UEFI grub.cfg.
EOF

# developer-qemu: ISOLINUX serial console + auto-boot (headless QEMU lab; no vesamenu hang).
write_developer_qemu_isolinux_serial_config() {
  write_text_file "${BOOTLOADER_DIR}/isolinux.cfg" 0644 <<'EOF'
# Setuphelfer developer-qemu — serial console + auto-boot (see QEMU_SERIAL_CAPTURE_AND_BOOTLOADER_OUTPUT_CONTRACT.md)
SERIAL 0 115200
CONSOLE 0
PROMPT 0
TIMEOUT 30
DEFAULT live-
ONTIMEOUT live-
include live.cfg
include install.cfg
EOF
}

# developer-qemu: patch GRUB cfg in binary stage if EFI/grub output exists (iso-hybrid).
write_developer_qemu_grub_serial_hook() {
  write_text_file "${BUILD_ROOT}/config/hooks/normal/095-developer-qemu-grub-serial.hook.binary" 0755 <<'EOF'
#!/bin/sh
set -eu
# Prepend serial terminal + short timeout to any grub.cfg produced during lb build.
GRUB_PREFIX='serial --unit=0 --speed=115200 --word=8 --parity=no --stop=1
terminal_input serial console
terminal_output serial console
set timeout=3
'
find binary -name 'grub.cfg' 2>/dev/null | while read -r cfg; do
  [ -f "$cfg" ] || continue
  if grep -q 'serial --unit=0' "$cfg" 2>/dev/null; then
    continue
  fi
  printf '%s\n' "$GRUB_PREFIX" | cat - "$cfg" > "${cfg}.tmp" && mv "${cfg}.tmp" "$cfg"
done
EOF
}

# developer-qemu: static wants symlinks (chroot systemctl enable is unreliable offline; matches backend/service pattern).
write_developer_qemu_autopilot_wants() {
  local wants="${BUILD_ROOT}/config/includes.chroot/etc/systemd/system/multi-user.target.wants"
  mkdir -p "$wants"
  ln -sf ../setuphelfer-qemu-smoke-autopilot.service "${wants}/setuphelfer-qemu-smoke-autopilot.service"
  ln -sf ../setuphelfer-serial-boot-markers.service "${wants}/setuphelfer-serial-boot-markers.service"
}

write_text_file "${BUILD_ROOT}/config/package-lists/setuphelfer.list.chroot" 0644 <<'EOF'
systemd
systemd-sysv
dbus
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
syslinux-utils
console-setup
keyboard-configuration
kbd
x11-xkb-utils
locales
tzdata
firmware-iwlwifi
firmware-intel-sound
wireless-regdb
network-manager
EOF

# lb_binary_iso runs isohybrid inside the live-build chroot (not the host). Debian ships
# isohybrid in syslinux-utils; lb_binary_iso only auto-installs syslinux (wrong package).
# *.list.binary is consumed by lb_binary_package-lists (ISO pool only), not the chroot.
write_text_file "${BUILD_ROOT}/config/package-lists/setuphelfer.list.binary" 0644 <<'EOF'
syslinux-utils
grub-efi-amd64-bin
grub-common
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

SYSTEMD_WANTS="${BUILD_ROOT}/config/includes.chroot/etc/systemd/system/multi-user.target.wants"
mkdir -p "$SYSTEMD_WANTS"
ln -sf ../setuphelfer-backend.service "${SYSTEMD_WANTS}/setuphelfer-backend.service"
ln -sf ../setuphelfer.service "${SYSTEMD_WANTS}/setuphelfer.service"

write_text_file "${BUILD_ROOT}/config/includes.chroot/etc/live/config.conf.d/10-setuphelfer-rescue.conf" 0644 <<'EOF'
# Rescue-Live: Nutzer/Hostname per Kernel cmdline (auto/config --bootappend-live).
# Standard Debian-Live: username=user, Passwort "live" (live-config).
LIVE_HOSTNAME="setuphelfer-rescue"
LIVE_USERNAME="user"
EOF

write_text_file "${BUILD_ROOT}/config/includes.chroot/etc/default/keyboard" 0644 <<'EOF'
XKBMODEL="pc105"
XKBLAYOUT="de"
XKBVARIANT=""
XKBOPTIONS=""
BACKSPACE="guess"
EOF

write_text_file "${BUILD_ROOT}/config/includes.chroot/etc/vconsole.conf" 0644 <<'EOF'
KEYMAP=de-latin1
FONT=
FONT_MAP=
FONT_UNIMAP=
EOF

write_text_file "${BUILD_ROOT}/config/preseeds/keyboard.seed.chroot" 0644 <<'EOF'
keyboard-configuration keyboard-configuration/layoutcode string de
keyboard-configuration keyboard-configuration/modelcode string pc105
keyboard-configuration keyboard-configuration/variant select
keyboard-configuration keyboard-configuration/options code
keyboard-configuration keyboard-configuration/unsupported config handled
keyboard-configuration keyboard-configuration/unsupported_layout skip
keyboard-configuration keyboard-configuration/unsupported_config_options skip
EOF

write_text_file "${BUILD_ROOT}/config/includes.chroot/etc/X11/Xsession.d/99-setuphelfer-keyboard-de" 0755 <<'EOF'
#!/bin/sh
# Force German X11 layout (QWERTZ) — live-config may lag behind login.
if command -v setxkbmap >/dev/null 2>&1; then
  setxkbmap -layout de -model pc105 -option "" 2>/dev/null || setxkbmap de 2>/dev/null || true
fi
EOF

write_text_file "${BUILD_ROOT}/config/includes.chroot/etc/systemd/system/setuphelfer-rescue-keyboard.service" 0644 <<'EOF'
[Unit]
Description=Setuphelfer Rescue German keyboard (console + X)
After=multi-user.target
ConditionPathExists=/etc/vconsole.conf

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/sh -c 'if command -v loadkeys >/dev/null 2>&1; then loadkeys de-latin1 2>/dev/null || loadkeys de 2>/dev/null || true; fi; if command -v setxkbmap >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then setxkbmap -layout de -model pc105 2>/dev/null || true; fi'

[Install]
WantedBy=multi-user.target
EOF

write_text_file "${BUILD_ROOT}/config/includes.chroot/etc/locale.gen" 0644 <<'EOF'
de_DE.UTF-8 UTF-8
en_US.UTF-8 UTF-8
EOF

write_text_file "${BUILD_ROOT}/config/includes.chroot/etc/default/locale" 0644 <<'EOF'
LANG=de_DE.UTF-8
LANGUAGE=de_DE:de
LC_ALL=
EOF

write_text_file "${BUILD_ROOT}/config/includes.chroot/etc/timezone" 0644 <<'EOF'
Europe/Berlin
EOF

# tzdata in chroot provides /usr/share/zoneinfo/Europe/Berlin at image build time.
ln -sf /usr/share/zoneinfo/Europe/Berlin \
  "${BUILD_ROOT}/config/includes.chroot/etc/localtime"

write_text_file "${BUILD_ROOT}/config/includes.chroot/etc/issue" 0644 <<'EOF'
Setuphelfer Rescue Live
Login: user  Passwort: live  (root-Konsole ist gesperrt)
Bundle: /opt/setuphelfer-rescue
Backend: systemctl status setuphelfer-backend.service
         curl -sS http://127.0.0.1:8000/api/version
Tastatur: de (Konsole de-latin1)
EOF

write_text_file "${BUILD_ROOT}/config/includes.chroot/etc/motd" 0644 <<'EOF'
Setuphelfer Rescue Live
Login: user / Passwort: live
Pfad: /opt/setuphelfer-rescue
Backend: systemctl status setuphelfer-backend.service
         curl -sS http://127.0.0.1:8000/api/version
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
systemctl enable setuphelfer-rescue-keyboard.service || true
systemctl enable setuphelfer-backend.service || true
systemctl enable setuphelfer.service || true
EOF

write_rescue_dev_agent_service() {
  local qemu_fallback="${1:-false}"
  local exec_start="/usr/bin/python3 -m backend.devserver_agent.cli --send --json"
  if [[ "$qemu_fallback" == "true" ]]; then
    exec_start="${exec_start} --qemu-host-fallback"
  fi
  write_text_file "${BUILD_ROOT}/config/includes.chroot/etc/systemd/system/setuphelfer-dev-agent.service" 0644 <<EOF
[Unit]
Description=Setuphelfer Development Agent (Rescue Developer Edition)
After=network-online.target setuphelfer-backend.service
Wants=network-online.target

[Service]
Type=oneshot
EnvironmentFile=-/etc/setuphelfer/setuphelfer-dev-agent.env
WorkingDirectory=/opt/setuphelfer-rescue/backend
Environment=PYTHONPATH=/opt/setuphelfer-rescue/backend:/opt/setuphelfer-rescue
Environment=SETUPHELFER_RESCUE_ROOT=/opt/setuphelfer-rescue
ExecStart=${exec_start}
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/opt/setuphelfer-rescue/docs/evidence/runtime-results/dev-agent-spool /tmp /run

[Install]
WantedBy=multi-user.target
EOF
}

copy_profile_overlay() {
  local profile_root="$1"
  local includes="${profile_root}/includes.chroot"
  local hooks="${profile_root}/hooks/normal"
  if [[ -d "$includes" ]]; then
    rsync -rlpt "${includes}/" "${BUILD_ROOT}/config/includes.chroot/"
  fi
  if [[ -d "$hooks" ]]; then
    mkdir -p "${BUILD_ROOT}/config/hooks/normal"
    rsync -rlpt "${hooks}/" "${BUILD_ROOT}/config/hooks/normal/"
  fi
}

write_dev_agent_enable_hook() {
  local enable_dev_agent="${1:-true}"
  if [[ "$enable_dev_agent" == "true" ]]; then
    write_text_file "${BUILD_ROOT}/config/hooks/normal/010-enable-setuphelfer-services.hook.chroot" 0755 <<'EOF'
#!/bin/sh
set -eu
systemctl enable systemd-networkd.service || true
systemctl enable setuphelfer-rescue-keyboard.service || true
systemctl enable setuphelfer-backend.service || true
systemctl enable setuphelfer.service || true
systemctl enable setuphelfer-dev-agent.service || true
EOF
  else
    write_text_file "${BUILD_ROOT}/config/hooks/normal/010-enable-setuphelfer-services.hook.chroot" 0755 <<'EOF'
#!/bin/sh
set -eu
systemctl enable systemd-networkd.service || true
systemctl enable setuphelfer-rescue-keyboard.service || true
systemctl enable setuphelfer-backend.service || true
systemctl enable setuphelfer.service || true
EOF
  fi
}

if [[ "${RESCUE_BUILD_PROFILE}" == "developer" || "${RESCUE_BUILD_PROFILE}" == "developer-qemu" ]]; then
  if [[ "${RESCUE_BUILD_PROFILE}" == "developer-qemu" ]]; then
    DEV_PROFILE_ROOT="${REPO_ROOT}/build/rescue/profiles/developer-qemu"
  else
    DEV_PROFILE_ROOT="${REPO_ROOT}/build/rescue/profiles/developer"
  fi
  [[ -f "${DEV_PROFILE_ROOT}/environment/setuphelfer-dev-agent.env" ]] || die "profile env missing: ${DEV_PROFILE_ROOT}"
  [[ -f "${DEV_PROFILE_ROOT}/manifest.json" ]] || die "profile manifest missing: ${DEV_PROFILE_ROOT}"
  mkdir -p "${BUILD_ROOT}/config/includes.chroot/etc/setuphelfer"
  copy_host_file "${DEV_PROFILE_ROOT}/environment/setuphelfer-dev-agent.env" \
    "${BUILD_ROOT}/config/includes.chroot/etc/setuphelfer/setuphelfer-dev-agent.env" 0644
  if [[ "${RESCUE_BUILD_PROFILE}" == "developer-qemu" ]]; then
    write_rescue_dev_agent_service true
    copy_profile_overlay "${DEV_PROFILE_ROOT}"
    write_developer_qemu_autopilot_wants
    write_dev_agent_enable_hook false
  else
    write_rescue_dev_agent_service false
    write_dev_agent_enable_hook true
  fi
  profile_id="rescue_developer_local_lab"
  if [[ "${RESCUE_BUILD_PROFILE}" == "developer-qemu" ]]; then
    profile_id="rescue_developer_qemu_local_lab"
  fi
  write_text_file "${BUILD_ROOT}/config/includes.chroot/opt/setuphelfer-rescue/config/rescue-developer-profile.json" 0644 <<EOF
{
  "profile_id": "${profile_id}",
  "profile_type": "${RESCUE_BUILD_PROFILE}",
  "agent_enabled": true,
  "agent_mode": "local_lab",
  "developer_auto_upload": true,
  "ssh_allowed": false,
  "write_actions_allowed": false,
  "source_head": "${SOURCE_HEAD}"
}
EOF
fi

LIVE_BOOTAPPEND='boot=live components init=/lib/systemd/systemd quiet splash setuphelfer_rescue=1 hostname=setuphelfer-rescue username=user user-fullname=Setuphelfer Rescue keyboard-layouts=de locales=de_DE.UTF-8 timezone=Europe/Berlin'
if [[ "${RESCUE_BUILD_PROFILE}" == "developer-qemu" ]]; then
  write_developer_qemu_isolinux_serial_config
  write_developer_qemu_grub_serial_hook
  # QEMU lab: serial + framebuffer, verbose kernel/systemd, no quiet/splash (see RESCUE_DEVELOPER_SERIAL_VISIBILITY_CONTRACT.md)
  LIVE_BOOTAPPEND='boot=live components init=/lib/systemd/systemd console=tty0 console=ttyS0,115200n8 loglevel=7 systemd.log_level=debug systemd.show_status=true ignore_loglevel printk.devkmsg=on setuphelfer_rescue=1 hostname=setuphelfer-rescue username=user user-fullname=Setuphelfer Rescue keyboard-layouts=de locales=de_DE.UTF-8 timezone=Europe/Berlin'
fi

write_text_file "${BUILD_ROOT}/auto/config" 0755 <<EOF
#!/bin/sh
set -eu
LB_COMMON="--distribution bookworm \\
  --archive-areas main \\
  --binary-images iso-hybrid \\
  --zsync false \\
  --debian-installer false \\
  --security false \\
  --firmware-chroot false \\
  --firmware-binary false \\
  --mode debian \\
  --bootappend-live ${LIVE_BOOTAPPEND@Q} \\
  --iso-volume SETUPHELFER_RESCUE \\
  --iso-application Setuphelfer Rescue Live"
if lb config --help 2>/dev/null | grep -q '\-\-bootloaders'; then
  eval "lb config noauto \${LB_COMMON} --bootloaders syslinux,grub-efi"
else
  eval "lb config noauto \${LB_COMMON}"
fi
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
rm -f binary.iso binary.hybrid.iso binary.img binary*.zsync* 2>/dev/null || true
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
  "usb_write_allowed": false,
  "rescue_build_profile": "${RESCUE_BUILD_PROFILE}",
  "developer_agent_in_tree": $([ "${RESCUE_BUILD_PROFILE}" = "developer" ] || [ "${RESCUE_BUILD_PROFILE}" = "developer-qemu" ] && echo true || echo false),
  "qemu_serial_console_configured": $([ "${RESCUE_BUILD_PROFILE}" = "developer-qemu" ] && echo true || echo false),
  "qemu_smoke_autopilot_hook": $([ "${RESCUE_BUILD_PROFILE}" = "developer-qemu" ] && echo true || echo false),
  "qemu_autopilot_service_wanted": $([ "${RESCUE_BUILD_PROFILE}" = "developer-qemu" ] && echo true || echo false),
  "qemu_guest_devserver_endpoint": "http://10.0.2.2:8001",
  "uefi_x64_boot_configured": true,
  "uefi_boot_method": "live-build-grub-efi-or-post-patch",
  "uefi_post_patch_script": "scripts/rescue-live/patch-rescue-iso-uefi-x64.sh",
  "uefi_validator_script": "scripts/rescue-live/validate-rescue-iso-uefi-boot.sh"
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
2. Legacy-\`rsvg\`-Compat unter \`config/includes.chroot/usr/local/bin/rsvg\` (rsvg-convert)
3. Paketliste, systemd-networkd, local-only Services, Hooks
4. UEFI-x64: \`grub-efi-amd64-bin\` in \`setuphelfer.list.binary\`; \`auto/config\` nutzt \`--bootloaders syslinux,grub-efi\` wenn live-build es unterstützt

## UEFI-x64 nach Build (Pflicht vor USB/MSI-Test)

Wenn \`validate-rescue-iso-uefi-boot.sh\` auf der ISO rot ist (live-build 3.0 / nur ISOLINUX):

\`\`\`bash
./scripts/rescue-live/patch-rescue-iso-uefi-x64.sh --in-place binary.hybrid.iso
./scripts/rescue-live/validate-rescue-iso-uefi-boot.sh binary.hybrid.iso
\`\`\`

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
echo "OK: rescue_build_profile=${RESCUE_BUILD_PROFILE}"
echo "OK: bundle copied to includes.chroot/opt/setuphelfer-rescue (${BUNDLE_FILES} files ref)"
