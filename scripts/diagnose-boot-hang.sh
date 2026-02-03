#!/bin/bash
# PI-Installer: Boot-Hänger diagnostizieren
# Auf dem Pi ausführen (z.B. nach Login per SSH oder in rescue.target):
#   bash diagnose-boot-hang.sh
# Oder vom Laptop: ssh pi@raspberrypi.local 'bash -s' < scripts/diagnose-boot-hang.sh

OUT="${1:-/tmp/pi-boot-diagnose.txt}"

{
  echo "=== PI Boot-Diagnose $(date -Iseconds) ==="
  echo ""

  echo "--- Letzter Boot: letzte 250 Zeilen journalctl ---"
  journalctl -b -1 -n 250 --no-pager 2>/dev/null || journalctl -b -n 250 --no-pager

  echo ""
  echo "--- Fehlgeschlagene Units ---"
  systemctl --failed --no-pager 2>/dev/null

  echo ""
  echo "--- Aktive Jobs (während Boot) ---"
  systemctl list-jobs --no-pager 2>/dev/null

  echo ""
  echo "--- /etc/fstab ---"
  cat /etc/fstab 2>/dev/null

  echo ""
  echo "--- Boot-Partition cmdline.txt ---"
  for f in /boot/cmdline.txt /boot/firmware/cmdline.txt; do
    [ -f "$f" ] && { echo "($f)"; cat "$f"; echo ""; }
  done
} 2>&1 | tee "$OUT"

echo ""
echo "Ausgabe wurde nach $OUT geschrieben. Zum Anzeigen: cat $OUT"
echo "Auf den Laptop kopieren: scp pi@<PI-IP>:$OUT ."
