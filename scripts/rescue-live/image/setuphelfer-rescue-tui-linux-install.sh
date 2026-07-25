#!/bin/bash
# TUI Linux Mint install assistant — text-only path for Gabriel when GUI missing.
# shellcheck disable=SC1091
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=setuphelfer-rescue-common.sh
source "${SCRIPT_DIR}/setuphelfer-rescue-common.sh" 2>/dev/null || true

_wt="$(setuphelfer_rescue_whiptail_tty 2>/dev/null || echo /dev/tty)"

_msg() {
  whiptail --title "Setuphelfer — Linux-Installation" --msgbox "$1" 20 74 3>&1 1>"$_wt" 2>&3 || true
}

_find_logs_root() {
  local c
  for c in \
    /run/setuphelfer-rescue/media/SETUP_LOGS \
    /run/setuphelfer/esp-rw \
    /media/*/SETUP_LOGS \
    /media/*/SETUP_LOGS2
  do
    # shellcheck disable=SC2086
    for p in $c; do
      if [[ -d "$p/setuphelfer/iso-cache/linux_mint" ]]; then
        echo "$p"
        return 0
      fi
    done
  done
  return 1
}

_iso_status() {
  local root iso status sha_file expected actual
  root="$(_find_logs_root)" || { echo "missing|ISO-Cache nicht gefunden"; return 1; }
  iso="$(ls -1 "$root/setuphelfer/iso-cache/linux_mint/"*.iso 2>/dev/null | head -1 || true)"
  if [[ -z "$iso" || ! -f "$iso" ]]; then
    echo "missing|Keine Mint-ISO unter $root/setuphelfer/iso-cache/linux_mint/"
    return 1
  fi
  sha_file="$root/setuphelfer/iso-cache/linux_mint/sha256sum.txt"
  expected=""
  if [[ -f "$sha_file" ]]; then
    expected="$(awk '/cinnamon-64bit\.iso/{print $1; exit}' "$sha_file")"
  fi
  if [[ -f "$root/setuphelfer/iso-cache/linux_mint/iso-status.json" ]]; then
    expected="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("sha256") or "")' \
      "$root/setuphelfer/iso-cache/linux_mint/iso-status.json" 2>/dev/null || echo "$expected")"
  fi
  actual="$(sha256sum -b "$iso" 2>/dev/null | awk '{print $1}')"
  if [[ -n "$expected" && "$actual" == "$expected" ]]; then
    echo "valid|$iso|$actual"
    return 0
  fi
  if [[ -z "$expected" && -n "$actual" ]]; then
    echo "review|$iso|$actual"
    return 0
  fi
  echo "corrupt|$iso|expected=$expected actual=$actual"
  return 1
}

_nvme_summary() {
  python3 - <<'PY' 2>/dev/null || echo "NVMe-Liste nicht verfügbar"
import json, subprocess, hashlib
out = subprocess.check_output(["lsblk", "-J", "-o", "NAME,SIZE,MODEL,SERIAL,TYPE,TRAN,FSTYPE,LABEL,MOUNTPOINT"], text=True)
data = json.loads(out)
lines = []
for d in data.get("blockdevices") or []:
    if d.get("type") != "disk":
        continue
    name = d.get("name") or ""
    if not name.startswith("nvme"):
        continue
    serial = (d.get("serial") or "").strip()
    sh = hashlib.sha256(serial.encode()).hexdigest()[:12] if serial else "—"
    role = "windows_system?" if any(
        (c.get("fstype") or "").lower() == "ntfs" for c in (d.get("children") or [])
    ) else "linux_target?"
    if (d.get("tran") or "").lower() == "usb":
        role = "rescue_usb"
    lines.append(f"/dev/{name}  {d.get('size')}  {d.get('model') or ''}  hash…{sh}  [{role}]")
print("\n".join(lines) if lines else "Keine NVMe gefunden.")
PY
}

_request_mint_iso_boot() {
  # Prefer stick GRUB entry written by install-assistant patch; reboot into it.
  local marker="/run/setuphelfer-rescue/boot-next-mint-iso.flag"
  mkdir -p /run/setuphelfer-rescue 2>/dev/null || true
  cat >"$marker" <<EOF
{
  "schema_version": 1,
  "action": "reboot_to_mint_iso_grub",
  "requested_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "grub_title": "Linux Mint 22.2 Installer (ISO vom Stick)"
}
EOF
  if [[ -x "${SCRIPT_DIR}/setuphelfer-rescue-set-boot-next-mint-iso" ]]; then
    "${SCRIPT_DIR}/setuphelfer-rescue-set-boot-next-mint-iso" || true
  fi
  # Fallback: rewrite default on ESP grub if writable
  local esp grub
  for esp in /run/setuphelfer/esp-rw /run/live/medium; do
    grub="$esp/boot/grub/grub.cfg"
    if [[ -f "$grub" && -w "$grub" ]]; then
      if grep -q 'Linux Mint 22.2 Installer (ISO vom Stick)' "$grub"; then
        # set default to that entry index
        python3 - <<PY
from pathlib import Path
import re
p = Path("$grub")
text = p.read_text(encoding="utf-8", errors="replace")
titles = re.findall(r'menuentry "([^"]+)"', text)
idx = next((i for i,t in enumerate(titles) if t.startswith("Linux Mint 22.2 Installer")), None)
if idx is not None:
    text2, n = re.subn(r"(?m)^set default=\d+\s*$", f"set default={idx}", text, count=1)
    if n:
        p.write_text(text2, encoding="utf-8")
        print(f"default={idx}")
PY
      fi
    fi
  done
}

setuphelfer_rescue_tui_linux_install() {
  local st iso sha msg
  if ! command -v whiptail >/dev/null 2>&1; then
    echo "whiptail fehlt"
    return 1
  fi

  st="$(_iso_status)" || true
  status="${st%%|*}"
  rest="${st#*|}"
  case "$status" in
    valid)
      iso="${rest%%|*}"
      sha="${rest##*|}"
      msg="Mint-ISO bereit (SHA256 OK).\n\n${iso}\nSHA: ${sha:0:16}…"
      ;;
    review)
      iso="${rest%%|*}"
      msg="Mint-ISO gefunden, SHA nicht gegen Manifest geprüft.\n\n${iso}"
      ;;
    *)
      _msg "Linux-Installation nicht möglich.\n\n${rest}\n\nISO muss unter SETUP_LOGS/setuphelfer/iso-cache/linux_mint/ liegen."
      return 1
      ;;
  esac

  local disks
  disks="$(_nvme_summary)"
  if ! whiptail --title "Setuphelfer — Linux-Installation" --yesno \
    "${msg}\n\nErkannte Datenträger:\n${disks}\n\nWindows-NVMe bleibt geschützt.\nWeiter zum Mint-Installer (ISO vom Stick)?" \
    22 74 3>&1 1>"$_wt" 2>&3; then
    return 0
  fi

  if ! whiptail --title "Bestätigung" --yesno \
    "Nur die Linux-Ziel-NVMe darf beschrieben werden.\nWindows-System-NVMe NICHT wählen.\n\nJetzt in den offiziellen Mint-Installer neu starten?" \
    14 70 3>&1 1>"$_wt" 2>&3; then
    return 0
  fi

  _request_mint_iso_boot
  _msg "Nächster Boot: Linux Mint Installer vom Stick.\n\nIm Installer die Linux-Ziel-NVMe wählen (nicht Windows).\nNeustart folgt."
  sync
  systemctl reboot 2>/dev/null || reboot
}

# Allow direct invocation
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  setuphelfer_rescue_ensure_state_dir 2>/dev/null || true
  setuphelfer_rescue_tui_linux_install
fi
