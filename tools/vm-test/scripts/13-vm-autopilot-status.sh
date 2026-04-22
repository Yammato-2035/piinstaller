#!/usr/bin/env bash
# Schnell-Healthcheck für setuphelfer-a und setuphelfer-b (Host-seitig).
# Liefert pro VM:
# - VBox-Zustand + Boot-Reihenfolge + DVD-Medium
# - TCP-Check auf SSH-Port
# - SSH-Banner-Check
# - Key-Login-Check (optional, wenn SSH_KEY gesetzt/gefunden)
#
# Nutzung:
#   cd tools/vm-test
#   ./scripts/13-vm-autopilot-status.sh
#   SSH_KEY=~/.ssh/id_ed25519 ./scripts/13-vm-autopilot-status.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

require_cmd VBoxManage
require_cmd ssh

SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_ed25519}"
TARGETS="${VM_SSH_TARGETS:-setuphelfer-a:2222:volker setuphelfer-b:2223:volker}"

print_vm_state() {
  local vm="$1"
  echo "VM: $vm"
  local info
  info="$(VBoxManage showvminfo "$vm" --machinereadable 2>/dev/null || true)"
  if [[ -z "$info" ]]; then
    echo "  exists: no"
    return 0
  fi
  echo "  exists: yes"
  echo "$info" | awk -F= '
    $1=="VMState"{gsub(/"/,"",$2); print "  state: "$2}
    $1=="boot1"{gsub(/"/,"",$2); print "  boot1: "$2}
    $1=="boot2"{gsub(/"/,"",$2); print "  boot2: "$2}
    $1=="\"SATA-3-0\""{gsub(/"/,"",$2); print "  dvd-medium: "$2}
  '
}

check_ssh() {
  local host="$1" port="$2" user="$3"
  echo "  ssh-target: ${user}@${host}:${port}"
  if nc -z -w2 "$host" "$port" >/dev/null 2>&1; then
    echo "  tcp-port: open"
  else
    echo "  tcp-port: closed"
    return 0
  fi

  local banner_out
  banner_out="$(ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new -p "$port" "$user@$host" "echo banner-ok" 2>&1 || true)"
  if [[ "$banner_out" == *"banner-ok"* ]]; then
    echo "  ssh-banner: ok"
  elif [[ "$banner_out" == *"banner exchange"* || "$banner_out" == *"timed out"* ]]; then
    echo "  ssh-banner: timeout/no-banner"
  elif [[ "$banner_out" == *"Permission denied"* ]]; then
    echo "  ssh-banner: ok (auth failed)"
  else
    echo "  ssh-banner: unknown (${banner_out//$'\n'/; })"
  fi

  if [[ -f "$SSH_KEY" ]]; then
    if ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new -i "$SSH_KEY" -p "$port" "$user@$host" "true" >/dev/null 2>&1; then
      echo "  key-login: ok ($(basename "$SSH_KEY"))"
    else
      echo "  key-login: failed ($(basename "$SSH_KEY"))"
    fi
  else
    echo "  key-login: skipped (SSH_KEY not found: $SSH_KEY)"
  fi
}

echo "=== VM AUTOPILOT STATUS ==="
echo "time: $(date -Iseconds)"
echo

for spec in $TARGETS; do
  IFS=: read -r vm port user <<<"$spec"
  [[ -n "${vm:-}" && -n "${port:-}" && -n "${user:-}" ]] || continue
  print_vm_state "$vm"
  check_ssh "127.0.0.1" "$port" "$user"
  echo
done

echo "hint: set VM_SSH_TARGETS='setuphelfer-a:2222:volker setuphelfer-b:2223:volker'"
