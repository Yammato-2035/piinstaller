#!/bin/bash
# Shared helpers for Setuphelfer rescue live scripts (no secrets in logs).
set -euo pipefail

SETUPHELFER_RESCUE_STATE_DIR="${SETUPHELFER_RESCUE_STATE_DIR:-/run/setuphelfer-rescue}"
SETUPHELFER_RESCUE_TELEMETRY_SERVER="${SETUPHELFER_RESCUE_TELEMETRY_SERVER:-http://192.168.178.140:8001}"
SETUPHELFER_RESCUE_TELEMETRY_URL="${SETUPHELFER_RESCUE_TELEMETRY_URL:-$SETUPHELFER_RESCUE_TELEMETRY_SERVER}"
SETUPHELFER_RESCUE_TELEMETRY_HEALTH_URL="${SETUPHELFER_RESCUE_TELEMETRY_HEALTH_URL:-}"
SETUPHELFER_RESCUE_TELEMETRY_INGEST_URL="${SETUPHELFER_RESCUE_TELEMETRY_INGEST_URL:-}"
SETUPHELFER_RESCUE_WIFI_SSID="${SETUPHELFER_RESCUE_WIFI_SSID:-}"
SETUPHELFER_RESCUE_WIFI_SECURITY="${SETUPHELFER_RESCUE_WIFI_SECURITY:-}"
SETUPHELFER_RESCUE_WIFI_PSK_FILE="${SETUPHELFER_RESCUE_WIFI_PSK_FILE:-}"
SETUPHELFER_RESCUE_ISO_SHA256="${SETUPHELFER_RESCUE_ISO_SHA256:-}"

setuphelfer_rescue_ensure_state_dir() {
  mkdir -p "$SETUPHELFER_RESCUE_STATE_DIR"
  chmod 0750 "$SETUPHELFER_RESCUE_STATE_DIR" 2>/dev/null || true
}

setuphelfer_rescue_is_live() {
  [[ -d /run/live/medium ]] || grep -Eq 'setuphelfer_rescue=1|boot=live' /proc/cmdline 2>/dev/null
}

setuphelfer_rescue_boot_id() {
  if [[ -r /proc/sys/kernel/random/boot_id ]]; then
    tr -d '\n' < /proc/sys/kernel/random/boot_id
    return 0
  fi
  cat /etc/machine-id 2>/dev/null || echo "unknown-boot-id"
}

setuphelfer_rescue_is_qemu() {
  if command -v systemd-detect-virt >/dev/null 2>&1; then
    systemd-detect-virt -q && return 0
  fi
  grep -Eq 'QEMU|VirtualBox|VMware|Bochs|KVM' /sys/class/dmi/id/product_name 2>/dev/null
}

setuphelfer_rescue_has_interactive_tty() {
  [[ -t 0 && -t 1 ]] && [[ "${SETUPHELFER_RESCUE_FORCE_HEADLESS:-}" != "1" ]]
}

setuphelfer_rescue_write_json() {
  local dest="$1"
  local tmp
  tmp="$(mktemp "${dest}.XXXXXX")"
  cat >"$tmp"
  mv -f "$tmp" "$dest"
  chmod 0640 "$dest" 2>/dev/null || true
}

setuphelfer_rescue_payload_hash() {
  python3 - <<'PY'
import json, hashlib, sys
data = json.load(sys.stdin)
data.pop("payload_hash_sha256", None)
body = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
print(hashlib.sha256(body).hexdigest())
PY
}

setuphelfer_rescue_iso_sha256() {
  if [[ -f /run/live/medium/live/filesystem.squashfs.sha256 ]]; then
    awk '{print $1}' /run/live/medium/live/filesystem.squashfs.sha256
    return 0
  fi
  if [[ -n "$SETUPHELFER_RESCUE_ISO_SHA256" ]]; then
    printf '%s\n' "$SETUPHELFER_RESCUE_ISO_SHA256"
    return 0
  fi
  echo ""
}

setuphelfer_rescue_trim_url() {
  local url="$1"
  url="${url%/}"
  printf '%s' "$url"
}

setuphelfer_rescue_resolve_telemetry_urls() {
  local base
  base="$(setuphelfer_rescue_trim_url "${SETUPHELFER_RESCUE_TELEMETRY_URL:-$SETUPHELFER_RESCUE_TELEMETRY_SERVER}")"
  if [[ -z "$SETUPHELFER_RESCUE_TELEMETRY_HEALTH_URL" ]]; then
    SETUPHELFER_RESCUE_TELEMETRY_HEALTH_URL="${base}/api/rescue/telemetry/health"
  fi
  if [[ -z "$SETUPHELFER_RESCUE_TELEMETRY_INGEST_URL" ]]; then
    SETUPHELFER_RESCUE_TELEMETRY_INGEST_URL="${base}/api/rescue/telemetry/v1/ingest"
  fi
  export SETUPHELFER_RESCUE_TELEMETRY_HEALTH_URL SETUPHELFER_RESCUE_TELEMETRY_INGEST_URL
}

setuphelfer_rescue_source_env_file() {
  local file="$1"
  [[ -r "$file" ]] || return 1
  # shellcheck disable=SC1090
  set -a
  source "$file"
  set +a
  return 0
}

setuphelfer_rescue_load_network_env() {
  local candidate
  for candidate in \
    /run/setuphelfer-rescue/network.env \
    /etc/setuphelfer-rescue/network.env \
    /run/setuphelfer/rescue-network.env; do
    setuphelfer_rescue_source_env_file "$candidate" && break
  done

  local mount_glob
  for mount_glob in /media/*/SETUPHELFER_CONFIG/network.env /media/*/SETUPHELFER_RESCUE_CONFIG/network.env; do
    [[ -e "$mount_glob" ]] || continue
    setuphelfer_rescue_source_env_file "$mount_glob" && break
  done

  if [[ -n "${SETUPHELFER_RESCUE_TELEMETRY_SERVER:-}" ]]; then
    SETUPHELFER_RESCUE_TELEMETRY_URL="${SETUPHELFER_RESCUE_TELEMETRY_SERVER}"
  fi
  setuphelfer_rescue_resolve_telemetry_urls
  export SETUPHELFER_RESCUE_TELEMETRY_URL SETUPHELFER_RESCUE_WIFI_SSID SETUPHELFER_RESCUE_WIFI_SECURITY SETUPHELFER_RESCUE_WIFI_PSK_FILE
}

setuphelfer_rescue_wifi_connect_configured() {
  local ssid="$SETUPHELFER_RESCUE_WIFI_SSID"
  [[ -n "$ssid" ]] || return 1
  nmcli radio wifi on 2>/dev/null || true
  rfkill unblock wifi 2>/dev/null || true
  if [[ -n "$SETUPHELFER_RESCUE_WIFI_PSK_FILE" && -r "$SETUPHELFER_RESCUE_WIFI_PSK_FILE" ]]; then
    HISTFILE=/dev/null nmcli --ask dev wifi connect "$ssid" \
      password "$(cat "$SETUPHELFER_RESCUE_WIFI_PSK_FILE")" >/dev/null 2>&1 && return 0
  fi
  if nmcli -t -f NAME connection show 2>/dev/null | grep -Fx "$ssid" >/dev/null; then
    nmcli connection up "$ssid" >/dev/null 2>&1 && return 0
  fi
  return 1
}

setuphelfer_rescue_wifi_connect_known() {
  nmcli radio wifi on 2>/dev/null || true
  rfkill unblock wifi 2>/dev/null || true
  local conn
  while IFS= read -r conn; do
    [[ -n "$conn" ]] || continue
    nmcli connection up "$conn" >/dev/null 2>&1 && return 0
  done < <(nmcli -t -f NAME,TYPE connection show 2>/dev/null | awk -F: '$2=="802-11-wireless"{print $1}' | head -5)
  return 1
}

setuphelfer_rescue_wizard_state_path() {
  printf '%s/wizard-state.json' "$SETUPHELFER_RESCUE_STATE_DIR"
}

setuphelfer_rescue_wizard_load_state() {
  local path
  path="$(setuphelfer_rescue_wizard_state_path)"
  [[ -f "$path" ]] || return 1
  cat "$path"
}

setuphelfer_rescue_wizard_save_state() {
  setuphelfer_rescue_write_json "$(setuphelfer_rescue_wizard_state_path)"
}

setuphelfer_rescue_show_branding() {
  local branding="/usr/share/setuphelfer/rescue/boot-branding.txt"
  [[ -f "$branding" ]] && cat "$branding" || echo "Setuphelfer Rettungsstick"
}

setuphelfer_rescue_wifi_prepare_radio() {
  nmcli radio wifi on 2>/dev/null || true
  rfkill unblock wifi 2>/dev/null || true
}

setuphelfer_rescue_wifi_scan_list() {
  local attempt max="${1:-3}"
  local -n _out=$2
  _out=()
  setuphelfer_rescue_wifi_prepare_radio
  for attempt in $(seq 1 "$max"); do
    nmcli device wifi rescan 2>/dev/null || true
    sleep 2
    mapfile -t _out < <(
      nmcli -t -f IN-USE,SSID,SECURITY,BARS device wifi list 2>/dev/null \
        | awk -F: '$2 != "--" && $2 != "" {print $2 "|" $3 "|" $4}' \
        | sort -u \
        | head -25
    )
    [[ "${#_out[@]}" -gt 0 ]] && return 0
  done
  return 12
}

setuphelfer_rescue_wifi_connect_ssid() {
  local ssid="$1"
  local hidden="${2:-0}"
  local psk="${3:-}"
  [[ -n "$ssid" ]] || return 13
  setuphelfer_rescue_wifi_prepare_radio
  if [[ -n "$psk" ]]; then
    if [[ "$hidden" == "1" ]]; then
      nmcli dev wifi connect "$ssid" password "$psk" hidden yes >/dev/null 2>&1
    else
      nmcli dev wifi connect "$ssid" password "$psk" >/dev/null 2>&1
    fi
  else
    if [[ "$hidden" == "1" ]]; then
      HISTFILE=/dev/null nmcli --ask dev wifi connect "$ssid" hidden yes >/dev/null 2>&1
    else
      HISTFILE=/dev/null nmcli --ask dev wifi connect "$ssid" >/dev/null 2>&1
    fi
  fi
}

setuphelfer_rescue_wifi_scan_and_menu() {
  local -a _entries=()
  local _choice _idx _ssid _sec _bars _menu_args=()
  local _action _hidden_ssid _psk _rc=0

  if ! setuphelfer_rescue_wifi_scan_list 3 _entries; then
    if command -v whiptail >/dev/null 2>&1 && setuphelfer_rescue_has_interactive_tty; then
      whiptail --title "Setuphelfer WLAN" --msgbox "Keine WLAN-Netze gefunden.\n\nErneut scannen, verstecktes WLAN oder offline fortfahren." 12 70 3>&1 1>&2 2>&3 || true
      _action="$(whiptail --title "Setuphelfer WLAN" --menu "Option wählen" 14 70 6 \
        "rescan" "Erneut scannen" \
        "hidden" "Verstecktes WLAN eingeben" \
        "offline" "Offline fortfahren (Telemetrie wird gespoolt)" 3>&1 1>&2 2>&3)" || return 14
      case "$_action" in
        rescan) setuphelfer_rescue_wifi_scan_and_menu && return $? ;;
        hidden)
          _hidden_ssid="$(whiptail --title "Verstecktes WLAN" --inputbox "SSID eingeben:" 10 60 3>&1 1>&2 2>&3)" || return 14
          _psk="$(whiptail --title "WLAN-Passwort" --passwordbox "Passwort für $_hidden_ssid (nicht geloggt):" 10 70 3>&1 1>&2 2>&3)" || return 15
          setuphelfer_rescue_wifi_connect_ssid "$_hidden_ssid" 1 "$_psk" && return 0
          whiptail --title "Setuphelfer WLAN" --msgbox "Verbindung fehlgeschlagen. Bitte erneut versuchen." 10 60 3>&1 1>&2 2>&3 || true
          return 13
          ;;
        offline) return 20 ;;
        *) return 14 ;;
      esac
    fi
    return 12
  fi

  if ! command -v whiptail >/dev/null 2>&1 || ! setuphelfer_rescue_has_interactive_tty; then
    _ssid="${_entries[0]%%|*}"
    setuphelfer_rescue_wifi_connect_ssid "$_ssid" 0 ""
    return $?
  fi

  _menu_args=()
  for _idx in "${!_entries[@]}"; do
    IFS='|' read -r _ssid _sec _bars <<< "${_entries[$_idx]}"
    _menu_args+=("$((_idx + 1))" "${_ssid} (${_sec:-offen})")
  done
  _menu_args+=("H" "Verstecktes WLAN…")
  _menu_args+=("R" "Erneut scannen")
  _menu_args+=("O" "Offline fortfahren")

  while true; do
    _choice="$(whiptail --title "Setuphelfer WLAN" \
      --menu "Netzwerk wählen (OK bestätigt, Esc = Offline)" 22 78 14 \
      "${_menu_args[@]}" 3>&1 1>&2 2>&3)" || return 20
    case "$_choice" in
      R)
        setuphelfer_rescue_wifi_scan_list 2 _entries || continue
        _menu_args=()
        for _idx in "${!_entries[@]}"; do
          IFS='|' read -r _ssid _sec _bars <<< "${_entries[$_idx]}"
          _menu_args+=("$((_idx + 1))" "${_ssid} (${_sec:-offen})")
        done
        _menu_args+=("H" "Verstecktes WLAN…")
        _menu_args+=("R" "Erneut scannen")
        _menu_args+=("O" "Offline fortfahren")
        continue
        ;;
      O) return 20 ;;
      H)
        _hidden_ssid="$(whiptail --title "Verstecktes WLAN" --inputbox "SSID:" 10 60 3>&1 1>&2 2>&3)" || continue
        _psk="$(whiptail --title "WLAN-Passwort" --passwordbox "Passwort (nicht geloggt):" 10 70 3>&1 1>&2 2>&3)" || continue
        setuphelfer_rescue_wifi_connect_ssid "$_hidden_ssid" 1 "$_psk" && return 0
        whiptail --title "Setuphelfer WLAN" --msgbox "Verbindung fehlgeschlagen." 10 50 3>&1 1>&2 2>&3 || true
        continue
        ;;
      *)
        _idx=$((_choice - 1))
        if [[ "$_idx" -lt 0 || "$_idx" -ge "${#_entries[@]}" ]]; then
          continue
        fi
        _ssid="${_entries[_idx]%%|*}"
        _psk="$(whiptail --title "WLAN-Passwort" --passwordbox "Passwort für:\n$_ssid\n(nicht geloggt)" 12 70 3>&1 1>&2 2>&3)" || continue
        if setuphelfer_rescue_wifi_connect_ssid "$_ssid" 0 "$_psk"; then
          return 0
        fi
        whiptail --title "Setuphelfer WLAN" --msgbox "Verbindung fehlgeschlagen.\nAnderes Netz wählen oder offline fortfahren." 10 60 3>&1 1>&2 2>&3 || true
        ;;
    esac
  done
}

setuphelfer_rescue_wait_default_route() {
  local attempt
  for attempt in $(seq 1 30); do
    ip route show default 2>/dev/null | grep -q . && return 0
    sleep 2
  done
  return 1
}
