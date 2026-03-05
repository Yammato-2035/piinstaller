#!/usr/bin/env bash
set -euo pipefail

TS="$(date +%Y%m%d_%H%M%S)"
OUT="/tmp/boot-kernel-nvme-debug-$TS.log"

exec > >(tee "$OUT") 2>&1

echo "=== BASIC ==="
date -Iseconds
uname -a
echo
echo "--- /proc/cmdline ---"
cat /proc/cmdline
echo
echo "--- mounts ---"
findmnt -no SOURCE /
findmnt -no SOURCE /boot/firmware || true
echo

echo "=== EEPROM/FIRMWARE ==="
vcgencmd bootloader_version 2>/dev/null || true
echo
vcgencmd bootloader_config 2>/dev/null || true
echo
echo "--- vcgencmd get_config int ---"
vcgencmd get_config int 2>/dev/null || true
echo
echo "--- vcgencmd get_config str ---"
vcgencmd get_config str 2>/dev/null || true
echo

echo "=== BOOT FILES ==="
ls -la /boot /boot/firmware /boot/firmware.bak 2>/dev/null || true
echo
echo "--- key files ---"
for f in \
  /boot/firmware/config.txt \
  /boot/firmware/cmdline.txt \
  /boot/firmware/kernel_2712.img \
  /boot/firmware/initramfs_2712 \
  /boot/firmware.bak/config.txt \
  /boot/firmware.bak/cmdline.txt \
  /boot/firmware.bak/kernel_2712.img \
  /boot/vmlinuz-6.12.62+rpt-rpi-2712
do
  [ -e "$f" ] && stat "$f"
done
echo

echo "--- checksums ---"
sha256sum \
  /boot/firmware/kernel_2712.img \
  /boot/firmware.bak/kernel_2712.img \
  /boot/vmlinuz-6.12.62+rpt-rpi-2712 2>/dev/null || true
echo

echo "=== KERNEL EMBEDDED VERSION STRINGS ==="
python3 - <<'PY'
import gzip
import pathlib
import subprocess
import shlex

candidates = [
    "/boot/firmware/kernel_2712.img",
    "/boot/firmware.bak/kernel_2712.img",
    "/boot/vmlinuz-6.12.62+rpt-rpi-2712",
]

for p in candidates:
    pp = pathlib.Path(p)
    if not pp.exists():
        continue
    out = pathlib.Path("/tmp") / (pp.name.replace("/", "_") + ".Image")
    try:
        with gzip.open(pp, "rb") as fi, open(out, "wb") as fo:
            fo.write(fi.read())
        print(f"\n--- {p} ---")
        cmd = f"strings {shlex.quote(str(out))} | grep 'Linux version' | head -n 5"
        subprocess.run(cmd, shell=True, check=False)
    except Exception as e:
        print(f"{p}: {e}")
PY
echo

echo "=== PCIe/NVMe RUNTIME ==="
lspci -nn || true
echo
lsblk -o NAME,TYPE,FSTYPE,LABEL,UUID,MOUNTPOINTS,SIZE,MODEL || true
echo
ls /dev/nvme* 2>/dev/null || echo "No /dev/nvme*"
echo
nvme list 2>/dev/null || true
echo

echo "=== BOOT LOGS (current boot) ==="
journalctl -k -b --no-pager | grep -Ei "Linux version|Kernel command line|pcie|nvme|subordinate|cannot be assigned|kexec" || true
echo

echo "=== SEARCH FOR FORCED CMDLINE/KERNEL STRINGS ==="
grep -R -nE "pcie_bus_safe|numa=fake=8|iommu_dma_numa_policy|nvme.max_host_mem_size_mb|kernel_2712.img|v8-16k" /boot /etc /usr/lib 2>/dev/null | head -n 300 || true
echo

echo "=== DONE ==="
echo "LOGFILE: $OUT"
