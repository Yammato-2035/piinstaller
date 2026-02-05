#!/bin/bash
# PI-Installer: LAN (Ethernet) verbindet nicht – Diagnose
# Auf dem Pi ausführen:
#   bash scripts/diagnose-lan.sh
# Oder vom Laptop: ssh pi@pi5-gg.local 'bash -s' < scripts/diagnose-lan.sh

set -e

OUT="${1:-/tmp/pi-lan-diagnose.txt}"

# Ethernet-Interface finden (eth0, end0, enp0s*, enx* – nicht wlan)
get_eth_interface() {
  for iface in /sys/class/net/eth* /sys/class/net/end* /sys/class/net/enp* /sys/class/net/enx*; do
    [ -d "$iface" ] || continue
    name="${iface##*/}"
    case "$name" in
      wlan*|wlp*) continue ;;
    esac
    echo "$name"
    return 0
  done
  # Fallback: eth0 prüfen (klassischer Name auf dem Pi)
  [ -d /sys/class/net/eth0 ] && echo "eth0" && return 0
  return 1
}

ETH="$(get_eth_interface 2>/dev/null || true)"

{
  echo "=== PI LAN-Diagnose $(date -Iseconds) ==="
  echo ""

  echo "--- Alle Netzwerk-Interfaces (ip link) ---"
  ip link show 2>/dev/null || true

  echo ""
  echo "--- Ethernet-Interface ---"
  if [ -z "$ETH" ]; then
    echo "Kein Ethernet-Interface gefunden (eth0, end0, enp*, enx*)."
    echo "Mögliche Ursachen: USB-Ethernet nicht erkannt, Treiber fehlt, Gerät nur per WLAN."
  else
    echo "Gefunden: $ETH"
    echo ""
    echo "  Link-Status (ip link show $ETH):"
    ip link show "$ETH" 2>/dev/null || true
    echo ""
    echo "  Adressen (ip addr show $ETH):"
    ip addr show "$ETH" 2>/dev/null || true
    echo ""
    if [ -f "/sys/class/net/$ETH/carrier" ]; then
      carrier=$(cat "/sys/class/net/$ETH/carrier" 2>/dev/null || echo "?")
      if [ "$carrier" = "0" ]; then
        echo "  Carrier: 0 → Kabel nicht verbunden oder kein Link (Router/Port?)."
      elif [ "$carrier" = "1" ]; then
        echo "  Carrier: 1 → Kabel verbunden, Link vorhanden."
      fi
    fi
    if [ -f "/sys/class/net/$ETH/operstate" ]; then
      echo "  operstate: $(cat /sys/class/net/$ETH/operstate 2>/dev/null)"
    fi
    if command -v ethtool >/dev/null 2>&1; then
      echo ""
      echo "  ethtool $ETH:"
      ethtool "$ETH" 2>/dev/null || true
    fi
  fi

  echo ""
  echo "--- Kernel-Meldungen (dmesg, eth/Link/carrier) ---"
  dmesg 2>/dev/null | grep -iE 'eth|link|carrier|rpi.*net|genet|lan78' | tail -30 || true

  echo ""
  echo "--- DHCP/Netzwerk-Dienste ---"
  for svc in dhcpcd systemd-networkd NetworkManager; do
    if systemctl is-active --quiet "$svc" 2>/dev/null; then
      echo "  $svc: aktiv"
    else
      systemctl is-enabled "$svc" 2>/dev/null && echo "  $svc: enabled but not active" || true
    fi
  done
  if [ -n "$ETH" ] && [ -f /etc/dhcpcd.conf ]; then
    echo ""
    echo "  Relevante dhcpcd.conf (interface $ETH):"
    grep -E "interface $ETH|^interface " /etc/dhcpcd.conf 2>/dev/null || true
  fi

  echo ""
  echo "--- hostname -I (alle IPs) ---"
  hostname -I 2>/dev/null || true

  echo ""
  echo "--- Kurz-Checkliste ---"
  echo "  [ ] Ethernet-Kabel fest am Pi und am Router/Switch stecken"
  echo "  [ ] Andere Geräte am gleichen Router-Port getestet?"
  echo "  [ ] Pi-Netzteil ausreichend (5 V, min. 2.5 A für Pi 3/4)"
  echo "  [ ] Bei USB-Ethernet: anderes USB-Port / anderes Kabel testen"
} 2>&1 | tee "$OUT"

echo ""
echo "Ausgabe wurde nach $OUT geschrieben. Zum Anzeigen: cat $OUT"
echo "Auf den Laptop kopieren: scp pi@pi5-gg.local:$OUT ."
