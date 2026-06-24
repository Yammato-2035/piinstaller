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

setuphelfer_rescue_json_bool() {
  python3 -c 'import json,sys; print("true" if json.load(open(sys.argv[1])).get(sys.argv[2], False) else "false")' "$1" "$2" 2>/dev/null || echo false
}

setuphelfer_rescue_network_is_ok() {
  local json="${SETUPHELFER_RESCUE_STATE_DIR}/network-onboarding.json"
  if [[ -f "$json" ]]; then
    python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print("true" if (d.get("default_route_present") and (d.get("wifi_connected") or d.get("config_source") in ("ethernet_connected","already_connected","prepared_env","known_nm_profile","interactive_menu"))) else "false")' "$json" 2>/dev/null || echo false
    return 0
  fi
  if ip route show default 2>/dev/null | grep -q .; then
    echo true
  else
    echo false
  fi
}

setuphelfer_rescue_media_is_stable() {
  local json="${SETUPHELFER_RESCUE_STATE_DIR}/media-check.json"
  if [[ -f "$json" ]]; then
    python3 -c 'import json,sys; print(str(json.load(open(sys.argv[1])).get("live_media_runtime_stable", False)).lower())' "$json" 2>/dev/null || echo false
    return 0
  fi
  echo false
}

setuphelfer_rescue_ensure_telemetry_opt_in() {
  setuphelfer_rescue_ensure_state_dir
  touch "${SETUPHELFER_RESCUE_STATE_DIR}/telemetry-opt-in" 2>/dev/null || true
}

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
  if [[ -n "${SETUPHELFER_RESCUE_TTY:-}" && -c "${SETUPHELFER_RESCUE_TTY}" && -w "${SETUPHELFER_RESCUE_TTY}" ]]; then
    return 0
  fi
  [[ -t 0 && -t 1 ]] && [[ "${SETUPHELFER_RESCUE_FORCE_HEADLESS:-}" != "1" ]]
}

setuphelfer_rescue_whiptail_tty() {
  if [[ -n "${SETUPHELFER_RESCUE_TTY:-}" && -c "${SETUPHELFER_RESCUE_TTY}" ]]; then
    printf '%s' "$SETUPHELFER_RESCUE_TTY"
    return 0
  fi
  if [[ -c /dev/tty1 && -w /dev/tty1 ]]; then
    printf '%s' "/dev/tty1"
    return 0
  fi
  printf '%s' "/dev/tty"
}

setuphelfer_rescue_summarize_ui_status() {
  local status_file="${1:-/run/setuphelfer/rescue-ui-status.json}"
  python3 - <<PY
import json
import sys
from pathlib import Path

path = Path(${status_file@Q})
if not path.is_file():
    print("Status: noch nicht verfügbar.")
    raise SystemExit(0)
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except json.JSONDecodeError:
    print("Status: Datei konnte nicht gelesen werden.")
    raise SystemExit(0)

mode = data.get("display_mode") or "unbekannt"
visible = "ja" if data.get("menu_visible") else "nein"
reason = data.get("reason") or "—"
browser = data.get("browser_candidate") or "keiner"
started = "ja" if data.get("browser_started") else "nein"
server = "ja" if data.get("server_started") else "nein"
url = data.get("ui_url") or "—"

lines = [
    "Setuphelfer Rettungsstick — Kurzstatus",
    "",
    f"Anzeigemodus: {mode}",
    f"Menü sichtbar: {visible}",
    f"UI-Server läuft: {server}",
    f"Browser-Kandidat: {browser}",
    f"Browser gestartet: {started}",
    f"Hinweis: {reason}",
    "",
    f"Lokale UI: {url}",
]
print("\\n".join(lines))
PY
}

setuphelfer_rescue_network_result_message() {
  local rc="${1:-0}"
  local json="${SETUPHELFER_RESCUE_STATE_DIR}/network-onboarding.json"
  python3 - <<PY
import json
import sys
from pathlib import Path

rc = int(${rc@Q})
path = Path(${json@Q})
data = {}
if path.is_file():
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        pass

code = data.get("error_code") or ""
if code == "NMCLI_MISSING":
    print("NetworkManager (nmcli) ist nicht verfügbar.\\n\\nOffline-Modus — du kannst das Notmenü weiter nutzen.")
elif code == "WIFI_DEVICE_NOT_FOUND":
    print("Keine WLAN-Hardware erkannt.\\n\\nEthernet prüfen oder offline fortfahren.")
elif code == "OFFLINE_BY_OPERATOR":
    print("Offline gewählt. Netzwerk bleibt optional.")
elif code == "WIFI_CONNECT_FAILED":
    print("WLAN-Verbindung fehlgeschlagen.\\n\\nBitte erneut versuchen oder offline fortfahren.")
elif code == "NETWORKMANAGER_NOT_RUNNING":
    print("NetworkManager konnte nicht gestartet werden.\\n\\nOffline-Modus möglich.")
elif data.get("default_route_present"):
    print("Netzwerk verbunden.")
elif rc == 0:
    print("Netzwerk-Aktion beendet. Kein Fehler — zurück im Notmenü.")
else:
    print("Netzwerk-Aktion beendet (Prüfung empfohlen).\\n\\nOffline-Modus weiter möglich.")
PY
}

setuphelfer_rescue_run_network_interactive() {
  local tty="${1:-$(setuphelfer_rescue_whiptail_tty)}"
  local net_script
  net_script="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/setuphelfer-rescue-network-onboarding"
  export SETUPHELFER_RESCUE_TTY="$tty"
  touch /run/setuphelfer-rescue/network-user-requested 2>/dev/null || true
  local rc=0
  set +e
  "$net_script" --interactive
  rc=$?
  set +e
  local msg
  msg="$(setuphelfer_rescue_network_result_message "$rc")"
  if command -v whiptail >/dev/null 2>&1 && [[ -c "$tty" ]]; then
    whiptail --title "Setuphelfer Netzwerk" --msgbox "$msg" 16 72 3>&1 1>"$tty" 2>&3 || true
  else
    printf '%s\n' "$msg" >"$tty" 2>/dev/null || true
  fi
  return 0
}

setuphelfer_rescue_record_menu_evidence() {
  local action="${1:-unknown}"
  local status="${2:-ok}"
  local detail="${3:-}"
  local ev_script
  ev_script="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/setuphelfer-rescue-evidence.py"
  if [[ -f "$ev_script" ]]; then
    python3 "$ev_script" menu-action --action "$action" --status "$status" --detail "$detail" 2>/dev/null || true
  fi
}

setuphelfer_rescue_run_evidence_bundle() {
  local ev_script
  ev_script="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/setuphelfer-rescue-evidence.py"
  if [[ -f "$ev_script" ]]; then
    python3 "$ev_script" bundle 2>/dev/null || true
  fi
}

setuphelfer_rescue_r3_telemetry_spool() {
  local payload_file="${1:-}"
  local reason="${2:-unknown}"
  local event_id="${3:-}"
  local ev_script
  ev_script="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/setuphelfer-rescue-evidence.py"
  [[ -f "$payload_file" ]] || return 0
  [[ -f "$ev_script" ]] || return 0
  if [[ -n "$event_id" ]]; then
    python3 "$ev_script" telemetry-spool --payload "$payload_file" --reason "$reason" --event-id "$event_id" 2>/dev/null || true
  else
    python3 "$ev_script" telemetry-spool --payload "$payload_file" --reason "$reason" 2>/dev/null || true
  fi
}

setuphelfer_rescue_r3_telemetry_mark_sent() {
  local event_id="${1:-}"
  local http_status="${2:-200}"
  local ev_script
  ev_script="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/setuphelfer-rescue-evidence.py"
  [[ -n "$event_id" ]] || return 0
  [[ -f "$ev_script" ]] || return 0
  python3 "$ev_script" telemetry-mark-sent --event-id "$event_id" --http-status "$http_status" 2>/dev/null || true
}

setuphelfer_rescue_cmdline_has_start_assistant() {
  grep -Eq '(^| )setuphelfer_start_assistant=1( |$)' /proc/cmdline 2>/dev/null
}

setuphelfer_rescue_start_assistant_status_path() {
  printf '%s/start-assistant-status.json' "$SETUPHELFER_RESCUE_STATE_DIR"
}

setuphelfer_rescue_write_start_assistant_status() {
  setuphelfer_rescue_write_json "$(setuphelfer_rescue_start_assistant_status_path)"
}

setuphelfer_rescue_prepare_tty1() {
  local attempt
  for attempt in $(seq 1 45); do
    [[ -c /dev/tty1 ]] || { sleep 1; continue; }
    chvt 1 2>/dev/null || true
    if [[ -w /dev/tty1 ]]; then
      return 0
    fi
    sleep 1
  done
  return 1
}

# RS-P3V.3+: hide kernel/systemd console noise on framebuffer during GUI boot.
setuphelfer_rescue_blank_fb_tty() {
  local tty_num="${1:-1}"
  local tty_dev="/dev/tty${tty_num}"
  [[ -c "$tty_dev" ]] || return 0
  if command -v setterm >/dev/null 2>&1; then
    setterm -term linux -cursor off -blank force -powersave off -clear all </dev/null >"$tty_dev" 2>/dev/null || true
  fi
  printf '\033[2J\033[3J\033[H\033[0m' >"$tty_dev" 2>/dev/null || true
}

setuphelfer_rescue_show_start_assistant_fallback() {
  setuphelfer_rescue_show_branding
  cat <<'EOF'

Setuphelfer Startassistent — manueller Fallback

Der Assistent konnte nicht automatisch starten. Bitte manuell ausführen:

  sudo setuphelfer-rescue-start-assistant
  sudo setuphelfer-rescue-network-onboarding
  sudo setuphelfer-rescue-telemetry-push

EOF
}

setuphelfer_rescue_write_json() {
  local dest="$1"
  local tmp
  tmp="$(mktemp "${dest}.XXXXXX")"
  cat >"$tmp"
  mv -f "$tmp" "$dest"
  chmod 0640 "$dest" 2>/dev/null || true
}

setuphelfer_rescue_evidence_rw_usable() {
  local d="$1" t
  [[ -d "$d" ]] || return 1
  t="$d/.sh-rw-test.$$"
  if ( : >"$t" ) 2>/dev/null; then
    rm -f "$t" 2>/dev/null || true
    return 0
  fi
  return 1
}

# RS-P2J: prefer SETUP_LOGS rw mount (same strategy as boot-diagnostics), then live ESP.
setuphelfer_rescue_evidence_writable_base() {
  local cand logsdev dev m esp_rw="/run/setuphelfer/esp-rw"
  if mountpoint -q "$esp_rw" 2>/dev/null && setuphelfer_rescue_evidence_rw_usable "$esp_rw"; then
    printf '%s' "$esp_rw"
    return 0
  fi
  for cand in /dev/disk/by-partlabel/SETUPHELFER_LOGS /dev/disk/by-label/SETUP_LOGS /dev/disk/by-label/SETUPHELFER_LOGS; do
    if [[ -e "$cand" ]]; then
      logsdev="$(readlink -f "$cand" 2>/dev/null || echo "$cand")"
      mkdir -p "$esp_rw" 2>/dev/null || true
      if timeout 10 mount -t vfat -o rw,flush,umask=0022 "$logsdev" "$esp_rw" 2>/dev/null \
        && setuphelfer_rescue_evidence_rw_usable "$esp_rw"; then
        printf '%s' "$esp_rw"
        return 0
      fi
      umount "$esp_rw" 2>/dev/null || true
      break
    fi
  done
  for m in /run/live/medium /lib/live/mount/medium; do
    if mountpoint -q "$m" 2>/dev/null; then
      timeout 10 mount -o remount,rw "$m" 2>/dev/null || true
      if setuphelfer_rescue_evidence_rw_usable "$m"; then
        printf '%s' "$m"
        return 0
      fi
    fi
  done
  setuphelfer_rescue_fat_esp_mount
}

setuphelfer_rescue_fat_esp_mount() {
  local candidate
  for candidate in /run/setuphelfer/esp-rw /run/live/medium /lib/live/mount/medium /media/*/SETUPHELFER; do
    if [[ -d "$candidate/setuphelfer" || -d "$candidate/EFI" || -d "$candidate/setuphelfer/diagnostics" ]]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

setuphelfer_rescue_mirror_evidence_file() {
  local src="$1" rel="$2" base dst_dir dst
  [[ -f "$src" ]] || return 0
  base="$(setuphelfer_rescue_evidence_writable_base)" || return 0
  dst_dir="$(dirname "${base}/${rel}")"
  mkdir -p "$dst_dir" 2>/dev/null || return 0
  dst="${base}/${rel}"
  cp -f "$src" "$dst" 2>/dev/null || return 0
  sync -f "$dst" 2>/dev/null || sync "$dst" 2>/dev/null || true
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

setuphelfer_rescue_medium_version_json_path() {
  local candidate
  for candidate in \
    "/run/live/medium/setuphelfer/rescue/version.json" \
    "/lib/live/mount/medium/setuphelfer/rescue/version.json" \
    "/media/setuphelfer/rescue/version.json"; do
    if [[ -f "$candidate" ]]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

setuphelfer_rescue_show_version_banner() {
  local vpath
  vpath="$(setuphelfer_rescue_medium_version_json_path || true)"
  if [[ -z "$vpath" || ! -f "$vpath" ]]; then
    echo "Version: unbekannt (kein version.json auf Medium)"
    return 1
  fi
  python3 - "$vpath" <<'PY'
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
pv = str(data.get("project_version") or "?")
commit = str(data.get("git_commit") or "?")
if len(commit) > 12 and commit != "?":
    commit = commit[:12]
built = str(data.get("built_at") or "?")
if len(built) > 19 and built != "?":
    built = built[:19].replace("T", " ")
sha = str(data.get("squashfs_sha256") or "?")
if len(sha) > 16 and sha != "?":
    sha = f"{sha[:16]}…"
print(f"Version: {pv}")
print(f"Commit:  {commit}")
print(f"Build:   {built}")
print(f"SHA256:  {sha}")
PY
}

setuphelfer_rescue_wifi_ensure_managed() {
  local _line _dev _typ _state
  rfkill unblock wifi 2>/dev/null || true
  rfkill unblock all 2>/dev/null || true
  if lsmod 2>/dev/null | grep -q '^iwlwifi'; then
    :
  elif iw dev 2>/dev/null | grep -q Interface; then
    modprobe iwlwifi 2>/dev/null || true
    modprobe iwlmvm 2>/dev/null || true
  fi
  for _dev in $(iw dev 2>/dev/null | awk '/Interface/ {print $2}'); do
    [[ -n "$_dev" ]] || continue
    ip link set "$_dev" up 2>/dev/null || true
    nmcli device set "$_dev" managed yes 2>/dev/null || true
  done
  while IFS= read -r _line; do
    _dev="${_line%%:*}"
    _typ="${_line#*:}"
    _typ="${_typ%%:*}"
    _state="${_line##*:}"
    if [[ "$_typ" == "wifi" && -n "$_dev" ]]; then
      case "$_state" in
        unmanaged|unavailable|disconnected)
          nmcli device set "$_dev" managed yes 2>/dev/null || true
          ip link set "$_dev" up 2>/dev/null || true
          sleep 1
          ;;
      esac
    fi
  done < <(nmcli -t -f DEVICE,TYPE,STATE device status 2>/dev/null || true)
  if nmcli radio 2>/dev/null | grep -qi 'WIFI-HW.*missing'; then
    if iw dev 2>/dev/null | grep -q Interface; then
      systemctl restart NetworkManager 2>/dev/null || true
      sleep 2
    fi
  fi
}

setuphelfer_rescue_wifi_prepare_radio() {
  setuphelfer_rescue_wifi_ensure_managed
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
  local _wt
  _wt="$(setuphelfer_rescue_whiptail_tty)"

  if ! command -v nmcli >/dev/null 2>&1; then
    return 21
  fi

  if ! setuphelfer_rescue_wifi_scan_list 3 _entries; then
    if command -v whiptail >/dev/null 2>&1 && setuphelfer_rescue_has_interactive_tty; then
      whiptail --title "Setuphelfer WLAN" --msgbox "Keine WLAN-Netze gefunden.\n\nErneut scannen, verstecktes WLAN oder offline fortfahren." 12 70 3>&1 1>"$_wt" 2>&3 || true
      _action="$(whiptail --title "Setuphelfer WLAN" --menu "Option wählen" 14 70 6 \
        "rescan" "Erneut scannen" \
        "hidden" "Verstecktes WLAN eingeben" \
        "offline" "Offline fortfahren (Telemetrie wird gespoolt)" 3>&1 1>"$_wt" 2>&3)" || return 14
      case "$_action" in
        rescan) setuphelfer_rescue_wifi_scan_and_menu && return $? ;;
        hidden)
          _hidden_ssid="$(whiptail --title "Verstecktes WLAN" --inputbox "SSID eingeben:" 10 60 3>&1 1>"$_wt" 2>&3)" || return 14
          _psk="$(whiptail --title "WLAN-Passwort" --passwordbox "Passwort für $_hidden_ssid (nicht geloggt):" 10 70 3>&1 1>"$_wt" 2>&3)" || return 15
          setuphelfer_rescue_wifi_connect_ssid "$_hidden_ssid" 1 "$_psk" && return 0
          whiptail --title "Setuphelfer WLAN" --msgbox "Verbindung fehlgeschlagen. Bitte erneut versuchen." 10 60 3>&1 1>"$_wt" 2>&3 || true
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
      "${_menu_args[@]}" 3>&1 1>"$_wt" 2>&3)" || return 20
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
        _hidden_ssid="$(whiptail --title "Verstecktes WLAN" --inputbox "SSID:" 10 60 3>&1 1>"$_wt" 2>&3)" || continue
        _psk="$(whiptail --title "WLAN-Passwort" --passwordbox "Passwort (nicht geloggt):" 10 70 3>&1 1>"$_wt" 2>&3)" || continue
        setuphelfer_rescue_wifi_connect_ssid "$_hidden_ssid" 1 "$_psk" && return 0
        whiptail --title "Setuphelfer WLAN" --msgbox "Verbindung fehlgeschlagen." 10 50 3>&1 1>"$_wt" 2>&3 || true
        continue
        ;;
      *)
        _idx=$((_choice - 1))
        if [[ "$_idx" -lt 0 || "$_idx" -ge "${#_entries[@]}" ]]; then
          continue
        fi
        _ssid="${_entries[_idx]%%|*}"
        _psk="$(whiptail --title "WLAN-Passwort" --passwordbox "Passwort für:\n$_ssid\n(nicht geloggt)" 12 70 3>&1 1>"$_wt" 2>&3)" || continue
        if setuphelfer_rescue_wifi_connect_ssid "$_ssid" 0 "$_psk"; then
          return 0
        fi
        whiptail --title "Setuphelfer WLAN" --msgbox "Verbindung fehlgeschlagen.\nAnderes Netz wählen oder offline fortfahren." 10 60 3>&1 1>"$_wt" 2>&3 || true
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

setuphelfer_rescue_boot_state_path() {
  printf '%s/boot_state.json' "$SETUPHELFER_RESCUE_STATE_DIR"
}

setuphelfer_rescue_should_start_gui() {
  if grep -Eq '(^| )setuphelfer_mode=gui( |$)' /proc/cmdline 2>/dev/null; then
    return 0
  fi
  if grep -Eq '(^| )setuphelfer_kiosk=1( |$)' /proc/cmdline 2>/dev/null \
     && ! grep -Eq '(^| )setuphelfer_kiosk=0( |$)' /proc/cmdline 2>/dev/null \
     && ! grep -Eq '(^| )setuphelfer_mode=text( |$)' /proc/cmdline 2>/dev/null; then
    return 0
  fi
  return 1
}

setuphelfer_rescue_write_boot_state() {
  local phase="${1:-}"
  local py_backend="/opt/setuphelfer-rescue/backend"
  if [[ -d "$py_backend" ]]; then
    PYTHONPATH="${py_backend}:${PYTHONPATH:-}" python3 - <<PY 2>/dev/null || true
from core.rescue_boot_evidence import write_boot_state_files
write_boot_state_files(phase=${phase@Q})
PY
    setuphelfer_rescue_mirror_evidence_file \
      "/var/lib/setuphelfer-rescue/local/evidence/boot_state_redacted.json" \
      "setuphelfer/evidence/boot/boot_state_redacted.json" 2>/dev/null || true
    return 0
  fi
  setuphelfer_rescue_write_json "$(setuphelfer_rescue_boot_state_path)" <<EOF
{
  "schema_version": 1,
  "phase": "$phase",
  "selected_mode": "text",
  "kiosk_requested": false,
  "backup_execute_allowed": false
}
EOF
}

SETUPHELFER_GUI_START_LOG="${SETUPHELFER_GUI_START_LOG:-/run/setuphelfer/gui-start.log}"
SETUPHELFER_X11_LAUNCH_LOG="${SETUPHELFER_X11_LAUNCH_LOG:-/run/setuphelfer/x11-launch.log}"
SETUPHELFER_CHROMIUM_LAUNCH_LOG="${SETUPHELFER_CHROMIUM_LAUNCH_LOG:-/run/setuphelfer/chromium-launch.log}"

setuphelfer_rescue_forensic_log() {
  local logfile="$1" step="$2" detail="${3:-}" rel="${4:-}"
  local ts
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u)"
  [[ -n "$rel" ]] || rel="setuphelfer/logs/boot/$(basename "$logfile")"
  mkdir -p "$(dirname "$logfile")" /run/setuphelfer 2>/dev/null || true
  {
    printf '[%s]\n[%s]\n' "$ts" "$step"
    [[ -n "$detail" ]] && printf '[%s]\n' "$detail"
    printf '\n'
  } >>"$logfile"
  setuphelfer_rescue_mirror_evidence_file "$logfile" "$rel" 2>/dev/null || true
}

setuphelfer_rescue_x11_log() {
  setuphelfer_rescue_forensic_log "$SETUPHELFER_X11_LAUNCH_LOG" "$1" "${2:-}" "setuphelfer/logs/boot/x11-launch.log"
}

setuphelfer_rescue_chromium_log() {
  setuphelfer_rescue_forensic_log "$SETUPHELFER_CHROMIUM_LAUNCH_LOG" "$1" "${2:-}" "setuphelfer/logs/boot/chromium-launch.log"
}

setuphelfer_rescue_mirror_gui_forensic_logs() {
  setuphelfer_rescue_mirror_evidence_file "$SETUPHELFER_GUI_START_LOG" "setuphelfer/logs/boot/gui-start.log" 2>/dev/null || true
  setuphelfer_rescue_mirror_evidence_file "$SETUPHELFER_X11_LAUNCH_LOG" "setuphelfer/logs/boot/x11-launch.log" 2>/dev/null || true
  setuphelfer_rescue_mirror_evidence_file "$SETUPHELFER_CHROMIUM_LAUNCH_LOG" "setuphelfer/logs/boot/chromium-launch.log" 2>/dev/null || true
}

setuphelfer_rescue_gui_chain_log_init() {
  local log="$SETUPHELFER_GUI_START_LOG"
  local boot_id session_id ts
  boot_id="$(awk '{print $1}' /proc/sys/kernel/random/boot_id 2>/dev/null || echo unknown)"
  session_id="$(date -u +%Y%m%d_%H%M%S)_gui"
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u)"
  mkdir -p "$(dirname "$log")" /run/setuphelfer 2>/dev/null || true
  : >"$SETUPHELFER_X11_LAUNCH_LOG" 2>/dev/null || true
  : >"$SETUPHELFER_CHROMIUM_LAUNCH_LOG" 2>/dev/null || true
  {
    printf '[%s]\n[SESSION_META]\n[BOOT_ID=%s SESSION_ID=%s]\n\n' "$ts" "$boot_id" "$session_id"
  } >"$log"
  setuphelfer_rescue_x11_log "SESSION_META" "BOOT_ID=${boot_id} SESSION_ID=${session_id}"
  setuphelfer_rescue_chromium_log "SESSION_META" "BOOT_ID=${boot_id} SESSION_ID=${session_id}"
  setuphelfer_rescue_mirror_gui_forensic_logs
}

# RS-P2F/P2J: structured GUI chain log — /run/setuphelfer/gui-start.log (mirrored to SETUP_LOGS best-effort).
setuphelfer_rescue_gui_chain_log() {
  local step="$1"
  local result="${2:-}"
  local log="$SETUPHELFER_GUI_START_LOG"
  local ts
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u)"
  mkdir -p "$(dirname "$log")" /run/setuphelfer 2>/dev/null || true
  {
    printf '[%s]\n' "$ts"
    printf '[%s]\n' "$step"
    [[ -n "$result" ]] && printf '[%s]\n' "$result"
    printf '\n'
  } >>"$log"
  setuphelfer_rescue_mirror_evidence_file "$log" "setuphelfer/logs/boot/gui-start.log" 2>/dev/null || true
}

setuphelfer_rescue_gui_chain_log_display_ctx() {
  local tty_name="none"
  tty_name="$(tty 2>/dev/null || echo none)"
  setuphelfer_rescue_gui_chain_log "DISPLAY_CTX" \
    "DISPLAY=${DISPLAY:-} XAUTHORITY=${XAUTHORITY:-} USER=${USER:-root} TTY=${tty_name} PPID=${PPID:-} PGID=${PGID:-}"
}

setuphelfer_rescue_gui_chain_log_xorg_artifacts() {
  local found="" line
  for line in \
    "/var/log/Xorg.0.log" \
    "${HOME:-/root}/.local/share/xorg/Xorg.0.log" \
    "/root/.local/share/xorg/Xorg.0.log"; do
    if [[ -f "$line" ]]; then
      found="${found}${line};"
      setuphelfer_rescue_gui_chain_log "XORG_LOG_TAIL" "path=${line}"
      tail -n 20 "$line" 2>/dev/null | while IFS= read -r _l; do
        setuphelfer_rescue_gui_chain_log "XORG_LOG_LINE" "$_l"
      done || true
    fi
  done
  if [[ -z "$found" ]]; then
    setuphelfer_rescue_gui_chain_log "XORG_LOG_MISSING" "checked=/var/log/Xorg.0.log ~/.local/share/xorg/"
  fi
  if [[ -d /tmp/.X11-unix ]]; then
    setuphelfer_rescue_gui_chain_log "X11_UNIX" "sockets=$(ls -1 /tmp/.X11-unix 2>/dev/null | tr '\n' ',' || echo none)"
  else
    setuphelfer_rescue_gui_chain_log "X11_UNIX" "missing"
  fi
}

# RS-P2G: GUI health probes, TUI marker, kiosk VT helpers.
SETUPHELFER_RESCUE_TUI_ACTIVE_FILE="${SETUPHELFER_RESCUE_TUI_ACTIVE_FILE:-/run/setuphelfer/rescue-tui-active}"
SETUPHELFER_RESCUE_KIOSK_VT="${SETUPHELFER_RESCUE_KIOSK_VT:-2}"

setuphelfer_rescue_tui_mark_active() {
  mkdir -p /run/setuphelfer 2>/dev/null || true
  touch "$SETUPHELFER_RESCUE_TUI_ACTIVE_FILE" 2>/dev/null || true
}

setuphelfer_rescue_tui_mark_inactive() {
  rm -f "$SETUPHELFER_RESCUE_TUI_ACTIVE_FILE" 2>/dev/null || true
}

setuphelfer_rescue_tui_is_active() {
  [[ -f "$SETUPHELFER_RESCUE_TUI_ACTIVE_FILE" ]]
}

setuphelfer_rescue_http_ok() {
  local url="$1"
  local timeout_sec="${2:-2}"
  python3 - <<PY 2>/dev/null
import sys
import urllib.request
try:
    urllib.request.urlopen(${url@Q}, timeout=float(${timeout_sec@Q}))
    sys.exit(0)
except Exception:
    sys.exit(1)
PY
}

setuphelfer_rescue_chromium_running() {
  pgrep -f 'chromium.*rescue\.html' >/dev/null 2>&1 \
    || pgrep -f 'chromium-browser.*rescue\.html' >/dev/null 2>&1
}

setuphelfer_rescue_xorg_running() {
  pgrep -f '[X]org|X :0' >/dev/null 2>&1
}

setuphelfer_rescue_xorg_pid() {
  pgrep -f '[X]org|X :0' 2>/dev/null | head -1 || true
}

# RS-P2L: true only when Xorg is running and the display answers (not merely /tmp/.X11-unix).
setuphelfer_rescue_x11_ready() {
  setuphelfer_rescue_prepare_x11_env
  setuphelfer_rescue_xorg_running || return 1
  if command -v xdpyinfo >/dev/null 2>&1; then
    xdpyinfo -display "${DISPLAY:-:0}" >/dev/null 2>&1 || return 1
  elif [[ ! -S "/tmp/.X11-unix/X${DISPLAY#:}" ]]; then
    return 1
  fi
  return 0
}

setuphelfer_rescue_log_x11_binaries() {
  local _sx _xi _xo
  _sx="$(command -v startx 2>/dev/null || echo missing)"
  _xi="$(command -v xinit 2>/dev/null || echo missing)"
  _xo="$(command -v Xorg 2>/dev/null || echo missing)"
  setuphelfer_rescue_gui_chain_log "CHECK_X11_BINARIES" "startx=${_sx} xinit=${_xi} Xorg=${_xo}"
  setuphelfer_rescue_x11_log "CHECK_X11_BINARIES" "startx=${_sx} xinit=${_xi} Xorg=${_xo}"
  if [[ "$_xo" == "missing" ]]; then
    setuphelfer_rescue_x11_log "XORG_MISSING" "which=Xorg"
    setuphelfer_rescue_gui_chain_log "XORG_MISSING" "which=Xorg"
  else
    setuphelfer_rescue_x11_log "XORG_FOUND" "path=${_xo}"
    setuphelfer_rescue_gui_chain_log "XORG_FOUND" "binary=${_xo}"
  fi
}

setuphelfer_rescue_xauthority_prepare() {
  local xauth="/run/setuphelfer/.Xauthority"
  mkdir -p /run/setuphelfer 2>/dev/null || true
  export DISPLAY="${DISPLAY:-:0}"
  export XAUTHORITY="${XAUTHORITY:-$xauth}"
  if touch "$XAUTHORITY" 2>/dev/null && [[ -f "$XAUTHORITY" ]]; then
    setuphelfer_rescue_x11_log "XAUTHORITY_READY" "path=${XAUTHORITY}"
    setuphelfer_rescue_gui_chain_log "XAUTHORITY_READY" "path=${XAUTHORITY}"
    return 0
  fi
  setuphelfer_rescue_x11_log "XAUTHORITY_MISSING" "path=${xauth}"
  setuphelfer_rescue_gui_chain_log "XAUTHORITY_MISSING" "path=${xauth}"
  return 1
}

setuphelfer_rescue_x11_log_xorg_pid() {
  local pid
  pid="$(setuphelfer_rescue_xorg_pid)"
  if [[ -n "$pid" ]]; then
    setuphelfer_rescue_x11_log "XORG_PID" "pid=${pid}"
    setuphelfer_rescue_gui_chain_log "XORG_PID" "pid=${pid}"
    return 0
  fi
  setuphelfer_rescue_x11_log "XORG_NOT_FOUND" "pgrep=empty"
  setuphelfer_rescue_gui_chain_log "XORG_NOT_FOUND" "pgrep=empty"
  return 1
}

setuphelfer_rescue_capture_x11_forensics() {
  local base session dest f
  base="$(setuphelfer_rescue_evidence_writable_base)" || return 0
  session="$(date -u +%Y%m%d_%H%M%S)_x11"
  dest="${base}/setuphelfer/logs/x11/${session}"
  mkdir -p "$dest" 2>/dev/null || return 0
  for f in \
    "/var/log/Xorg.0.log" \
    "${HOME:-/root}/.local/share/xorg/Xorg.0.log" \
    "/root/.local/share/xorg/Xorg.0.log"; do
    [[ -f "$f" ]] && cp -a "$f" "${dest}/" 2>/dev/null || true
  done
  if command -v journalctl >/dev/null 2>&1; then
    journalctl -b --no-pager 2>/dev/null | grep -Ei 'xorg|startx|xinit' >"${dest}/journal-xorg.txt" 2>/dev/null || true
  fi
  if [[ -d /tmp/.X11-unix ]]; then
    ls -la /tmp/.X11-unix >"${dest}/x11-unix-ls.txt" 2>/dev/null || true
  fi
  setuphelfer_rescue_mirror_evidence_file "${SETUPHELFER_X11_LAUNCH_LOG}" "setuphelfer/logs/boot/x11-launch.log" 2>/dev/null || true
  setuphelfer_rescue_gui_chain_log "X11_FORENSICS_CAPTURED" "dest=setuphelfer/logs/x11/${session}"
}

# Returns 0 only when backend, UI HTTP, display, and chromium are stable for min_sec.
setuphelfer_rescue_gui_health_ok() {
  local min_sec="${1:-5}"
  local port_ui="${SETUPHELFER_RESCUE_UI_PORT:-8765}"
  if ! setuphelfer_rescue_http_ok "http://127.0.0.1:8000/api/version"; then
    return 1
  fi
  if ! setuphelfer_rescue_http_ok "http://127.0.0.1:${port_ui}/rescue.html"; then
    return 2
  fi
  if ! setuphelfer_rescue_x11_ready; then
    return 3
  fi
  if ! setuphelfer_rescue_chromium_running; then
    return 4
  fi
  local elapsed=0
  while [[ "$elapsed" -lt "$min_sec" ]]; do
    if ! setuphelfer_rescue_chromium_running; then
      return 5
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done
  return 0
}

setuphelfer_rescue_run_on_kiosk_vt() {
  local vt="$SETUPHELFER_RESCUE_KIOSK_VT" _rc=0
  if command -v openvt >/dev/null 2>&1; then
    setuphelfer_rescue_gui_chain_log "OPENVT_START" "vt=${vt} cmd=$*"
    setuphelfer_rescue_x11_log "OPENVT_START" "vt=${vt} cmd=$*"
    openvt -f -s -w -c "$vt" -- "$@"
    _rc=$?
    if [[ "$_rc" -eq 0 ]]; then
      setuphelfer_rescue_gui_chain_log "OPENVT_OK" "vt=${vt} exit=0"
      setuphelfer_rescue_x11_log "OPENVT_OK" "vt=${vt} exit=0"
    else
      setuphelfer_rescue_gui_chain_log "OPENVT_FAIL" "vt=${vt} exit=${_rc}"
      setuphelfer_rescue_x11_log "OPENVT_FAIL" "vt=${vt} exit=${_rc}"
    fi
    return "$_rc"
  fi
  if [[ -c "/dev/tty${vt}" ]]; then
    chvt "$vt" 2>/dev/null || true
    setuphelfer_rescue_gui_chain_log "CHVT_EXEC" "vt=${vt} cmd=$*"
    setuphelfer_rescue_x11_log "CHVT_EXEC" "vt=${vt} cmd=$*"
    "$@"
    return $?
  fi
  setuphelfer_rescue_gui_chain_log "TTY_UNAVAILABLE" "vt=${vt}"
  setuphelfer_rescue_x11_log "TTY_UNAVAILABLE" "vt=${vt}"
  return 1
}

setuphelfer_rescue_prepare_x11_env() {
  export DISPLAY="${DISPLAY:-:0}"
  if [[ -z "${XAUTHORITY:-}" ]]; then
    if [[ -f "${HOME:-/root}/.Xauthority" ]]; then
      export XAUTHORITY="${HOME:-/root}/.Xauthority"
    elif [[ -f /run/setuphelfer/.Xauthority ]]; then
      export XAUTHORITY=/run/setuphelfer/.Xauthority
    fi
  fi
}

# RS-P2O: non-blocking backend bootstrap (GUI chain may start X11 in parallel).
setuphelfer_rescue_backend_start_async() {
  local log="${1:-/run/setuphelfer/gui-start.log}"
  local backend_start="${SETUPHELFER_RESCUE_SCRIPT_DIR:-/usr/local/sbin}/setuphelfer-rescue-backend-start.sh"
  if setuphelfer_rescue_http_ok "http://127.0.0.1:8000/api/version" 2; then
    setuphelfer_rescue_gui_chain_log "BACKEND_START" "async=skipped reason=already_up"
    return 0
  fi
  (
    if [[ -x "$backend_start" ]]; then
      "$backend_start" >>"$log" 2>&1
      _rc=$?
    else
      _rc=127
    fi
    setuphelfer_rescue_gui_chain_log "BACKEND_START" "async_done rc=${_rc}"
  ) &
  setuphelfer_rescue_gui_chain_log "BACKEND_START" "async_pid=$! log=${log}"
}
