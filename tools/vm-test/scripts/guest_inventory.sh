#!/usr/bin/env bash
set -Eeuo pipefail

echo "========================================"
echo "SETUPHELFER VM INVENTORY"
echo "Datum: $(date -Iseconds)"
echo "Hostname: $(hostname)"
echo "========================================"

echo
echo "[SYSTEM]"
uname -a || true
cat /etc/os-release || true

echo
echo "[UPTIME]"
uptime || true

echo
echo "[USER]"
whoami || true

echo
echo "[DISKS]"
lsblk -f || true

echo
echo "[MOUNTS]"
mount | head -50 || true

echo
echo "[DISK USAGE]"
df -h || true

echo
echo "[NETWORK]"
ip a || true

echo
echo "[SERVICES – SETUPHELFER]"
systemctl list-units 2>/dev/null | grep -i setuphelfer || true

echo
echo "[PROCESSES – SETUPHELFER]"
ps aux 2>/dev/null | grep -i '[s]etuphelfer' || ps aux 2>/dev/null | grep -i setuphelfer || true

echo
echo "[FILESYSTEM CHECK – MARKER]"
ls -lah /opt 2>/dev/null || true
ls -lah /home 2>/dev/null || true

echo
echo "[BACKUP TARGET CHECK]"
ls -lah /mnt 2>/dev/null || true

echo
echo "========================================"
echo "END OF REPORT"
echo "========================================"
