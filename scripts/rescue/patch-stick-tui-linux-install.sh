#!/usr/bin/env bash
# Patch stick squashfs TUI + GRUB for Gabriel text Linux-install path.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ESP_DEV="${1:-/dev/sda1}"
WORK="${TMPDIR:-/tmp}/setuphelfer-tui-patch-$$"
SQ_OUT="$WORK/filesystem.squashfs.new"

echo "============================================================"
echo "STICK TUI+GRUB PATCH — Linux-Installation Textpfad"
echo "ESP: $ESP_DEV  Repo: $ROOT"
echo "============================================================"

LABEL="$(lsblk -no LABEL "$ESP_DEV" 2>/dev/null || true)"
[[ "$LABEL" == "SETUPHELFER" ]] || { echo "refuse: label=$LABEL"; exit 3; }

mkdir -p "$WORK/root"
sudo mount -o rw "$ESP_DEV" /mnt/setuphelfer-rw 2>/dev/null || {
  sudo mkdir -p /mnt/setuphelfer-rw
  sudo mount -o rw "$ESP_DEV" /mnt/setuphelfer-rw
}
SQ=/mnt/setuphelfer-rw/live/filesystem.squashfs
[[ -f "$SQ" ]] || { echo "missing squashfs"; exit 4; }

# Free space: drop old prev if needed
if [[ -f /mnt/setuphelfer-rw/live/filesystem.squashfs.prev-1.10.0.59 ]]; then
  echo "Removing old prev payload to free ESP space…"
  sudo rm -f /mnt/setuphelfer-rw/live/filesystem.squashfs.prev-1.10.0.59
fi

echo "Extracting squashfs (slow)…"
unsquashfs -force -no-xattrs -d "$WORK/root" "$SQ" >/dev/null

SBIN="$WORK/root/usr/local/sbin"
install -m 0755 "$ROOT/scripts/rescue-live/image/setuphelfer-rescue-tui.sh" \
  "$SBIN/setuphelfer-rescue-tui"
# drop .sh suffix copy used by some callers
install -m 0755 "$ROOT/scripts/rescue-live/image/setuphelfer-rescue-tui.sh" \
  "$SBIN/setuphelfer-rescue-tui.sh" 2>/dev/null || true
install -m 0755 "$ROOT/scripts/rescue-live/image/setuphelfer-rescue-tui-linux-install.sh" \
  "$SBIN/setuphelfer-rescue-tui-linux-install"
install -m 0755 "$ROOT/scripts/rescue-live/image/setuphelfer-rescue-tui-linux-install.sh" \
  "$SBIN/setuphelfer-rescue-tui-linux-install.sh"

# sanity
grep -q 'Linux-Installation (Mint vom Stick)' "$SBIN/setuphelfer-rescue-tui" \
  || { echo "TUI patch missing menu label"; exit 5; }

echo "Repacking squashfs…"
mksquashfs "$WORK/root" "$SQ_OUT" -comp xz -noappend -no-exports >/dev/null
NEW_SHA="$(sha256sum "$SQ_OUT" | awk '{print $1}')"
echo "new_sha=$NEW_SHA"

# Backup current
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
sudo cp -a "$SQ" "/mnt/setuphelfer-rw/live/filesystem.squashfs.prev-tui-linux-$STAMP"
sudo cp -a "$SQ_OUT" "$SQ"
echo -n "$NEW_SHA" | sudo tee /mnt/setuphelfer-rw/live/filesystem.squashfs.sha256 >/dev/null
echo "" | sudo tee -a /mnt/setuphelfer-rw/live/filesystem.squashfs.sha256 >/dev/null

# Update version note (patch W bump locally on stick marker)
python3 - <<PY
import json
from datetime import datetime, timezone
from pathlib import Path
for rel in ("setuphelfer/rescue/version.json", "setuphelfer/version.json"):
    p = Path("/mnt/setuphelfer-rw") / rel
    if not p.is_file():
        continue
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        continue
    data["tui_linux_install_patched_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data["tui_linux_install"] = True
    data["filesystem_squashfs_sha256"] = "$NEW_SHA"
    data["payload_sha256"] = "$NEW_SHA"
    data["note"] = (str(data.get("note") or "") + "; tui_linux_install_menu").strip("; ")
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("updated", p)
PY

# GRUB regenerate
export PYTHONPATH="$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"
NEW_GRUB="$(python3 - <<'PY'
from core.rescue_install_assistant_grub import generate_gabriel_install_grub_cfg, validate_gabriel_install_grub
cfg = generate_gabriel_install_grub_cfg(fat_uuid="9BB9-A4A6")
assert validate_gabriel_install_grub(cfg)["ok"]
print(cfg, end="")
PY
)"
sudo cp -a /mnt/setuphelfer-rw/boot/grub/grub.cfg \
  "/mnt/setuphelfer-rw/boot/grub/grub.cfg.prev-pre-tui-linux-$STAMP"
printf '%s\n' "$NEW_GRUB" | sudo tee /mnt/setuphelfer-rw/boot/grub/grub.cfg >/dev/null

sync
sudo umount /mnt/setuphelfer-rw
rm -rf "$WORK"
echo "OK: TUI Linux-Install + Mint ISO GRUB entry written to stick"
echo "Gabriel: Default = Text-Installation; oder direkt 'Linux Mint 22.2 Installer (ISO vom Stick)'"
