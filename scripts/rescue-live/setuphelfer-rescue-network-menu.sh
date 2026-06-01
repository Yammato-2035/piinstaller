#!/usr/bin/env bash
# Rescue network + remote pairing menu (TTY). Secrets never logged or persisted by default.
set -euo pipefail

NET_ENV="/run/setuphelfer/rescue-network.env"
REMOTE_ENV="/run/setuphelfer/rescue-remote.env"
LOG_TAG="setuphelfer-rescue-network-menu"

mkdir -p /run/setuphelfer
chmod 700 /run/setuphelfer

write_env_kv() {
  local file="$1"
  shift
  : >"$file"
  chmod 600 "$file"
  while [[ $# -ge 2 ]]; do
    printf '%s=%q\n' "$1" "$2" >>"$file"
    shift 2
  done
}

menu() {
  echo "=== Setuphelfer Rescue — Netzwerk ==="
  echo "1) Offline (keine Verbindung)"
  echo "2) eth0 DHCP"
  echo "3) eth0 statische IP"
  echo "4) WLAN (SSID + Passwort)"
  echo "5) QEMU-Lab (10.0.2.2:8001)"
  echo "6) Manuelle Development-Server-URL"
  read -r -p "Auswahl [1-6]: " choice
  case "$choice" in
    1)
      write_env_kv "$NET_ENV" SETUPHELFER_NETWORK_MODE offline
      write_env_kv "$REMOTE_ENV" SETUPHELFER_REMOTE_ENABLED 0
      ;;
    2)
      if command -v nmcli >/dev/null 2>&1; then
        nmcli device connect eth0 >/dev/null 2>&1 || true
      elif command -v dhclient >/dev/null 2>&1; then
        ip link set eth0 up 2>/dev/null || true
        dhclient -v eth0 >/dev/null 2>&1 || true
      else
        echo "ERROR: nmcli/dhclient fehlt — kein apt in diesem Menü" >&2
        exit 1
      fi
      write_env_kv "$NET_ENV" SETUPHELFER_NETWORK_MODE eth0_dhcp SETUPHELFER_NET_IF eth0
      ;;
    3)
      read -r -p "IP/CIDR (z.B. 192.168.1.50/24): " static_ip
      read -r -p "Gateway: " gw
      if command -v nmcli >/dev/null 2>&1; then
        nmcli con add type ethernet ifname eth0 con-name setuphelfer-eth0-static \
          ipv4.addresses "$static_ip" ipv4.gateway "$gw" ipv4.method manual >/dev/null 2>&1 || true
        nmcli con up setuphelfer-eth0-static >/dev/null 2>&1 || true
      else
        echo "ERROR: nmcli fehlt für statische IP" >&2
        exit 1
      fi
      write_env_kv "$NET_ENV" SETUPHELFER_NETWORK_MODE eth0_static SETUPHELFER_NET_IF eth0 \
        SETUPHELFER_STATIC_IP "$static_ip" SETUPHELFER_GATEWAY "$gw"
      ;;
    4)
      if ! command -v nmcli >/dev/null 2>&1; then
        echo "ERROR: nmcli fehlt — WLAN nicht verfügbar ohne Toolinstallation" >&2
        exit 1
      fi
      nmcli device wifi rescan >/dev/null 2>&1 || true
      nmcli device wifi list | head -20
      read -r -p "SSID: " ssid
      read -r -s -p "WLAN-Passwort (nicht geloggt): " wifi_pass
      echo
      nmcli device wifi connect "$ssid" password "$wifi_pass" >/dev/null 2>&1 || {
        echo "WLAN-Verbindung fehlgeschlagen" >&2
        exit 1
      }
      # Passwort nicht in env-Dateien persistieren
      write_env_kv "$NET_ENV" SETUPHELFER_NETWORK_MODE wlan SETUPHELFER_WLAN_SSID "$ssid"
      ;;
    5)
      write_env_kv "$NET_ENV" SETUPHELFER_NETWORK_MODE qemu_lab \
        SETUPHELFER_DEV_SERVER_URL "http://10.0.2.2:8001"
      read -r -p "Remote-Control aktivieren (developer-qemu)? [y/N]: " en
      remote=0
      [[ "$en" == "y" || "$en" == "Y" ]] && remote=1
      read -r -p "Pairing-Token (optional, nicht geloggt): " -s token
      echo
      agent_id="rescue_$(date -u +%Y%m%d_%H%M%S)"
      write_env_kv "$REMOTE_ENV" \
        SETUPHELFER_REMOTE_ENABLED "$remote" \
        SETUPHELFER_DEV_SERVER_URL "http://10.0.2.2:8001" \
        SETUPHELFER_REMOTE_AGENT_ID "$agent_id" \
        SETUPHELFER_PAIRING_TOKEN "$token" \
        SETUPHELFER_REMOTE_READ_ONLY 1 \
        SETUPHELFER_REMOTE_WRITE_RUNBOOKS 0
      ;;
    6)
      read -r -p "Development-Server-URL: " url
      write_env_kv "$NET_ENV" SETUPHELFER_NETWORK_MODE manual_url SETUPHELFER_DEV_SERVER_URL "$url"
      read -r -p "Remote-Control aktivieren? [y/N]: " en
      remote=0
      [[ "$en" == "y" || "$en" == "Y" ]] && remote=1
      read -r -p "Pairing-Token (optional): " -s token
      echo
      agent_id="rescue_$(date -u +%Y%m%d_%H%M%S)"
      write_env_kv "$REMOTE_ENV" \
        SETUPHELFER_REMOTE_ENABLED "$remote" \
        SETUPHELFER_DEV_SERVER_URL "$url" \
        SETUPHELFER_REMOTE_AGENT_ID "$agent_id" \
        SETUPHELFER_PAIRING_TOKEN "$token" \
        SETUPHELFER_REMOTE_READ_ONLY 1 \
        SETUPHELFER_REMOTE_WRITE_RUNBOOKS 0
      ;;
    *)
      echo "Ungültige Auswahl" >&2
      exit 1
      ;;
  esac
  logger -t "$LOG_TAG" "network mode configured (no secrets logged)"
  echo "OK: Konfiguration in ${NET_ENV} und ${REMOTE_ENV}"
}

menu "$@"
