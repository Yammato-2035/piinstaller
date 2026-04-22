#!/usr/bin/env bash
# Auf dem **Linux-Host** in tools/vm-test: wartet auf SSH, synct Repo, startet in-guest-vmtest-autorun.sh.
#
# Voraussetzung auf dem Gast: einmalig NOPASSWD-sudo (siehe in-guest-vmtest-postinstall.sh).
#
# Beispiel:
#   cd tools/vm-test
#   SSH_KEY=~/.ssh/id_ed25519_pi SSH_GUEST_SPEC=127.0.0.1:2222:volker \
#   VMTEST_BACKUP_DEV=/dev/sdc ./scripts/host-vmtest-ssh-autorun.sh
#
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VM_TEST_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_ed25519}"
SSH_GUEST_SPEC="${SSH_GUEST_SPEC:-127.0.0.1:2222:volker}"
VMTEST_BACKUP_DEV="${VMTEST_BACKUP_DEV:-/dev/sdc}"

IFS=: read -r _host _port _user <<<"$SSH_GUEST_SPEC"
[[ -n "$_port" && -n "$_user" ]] || {
  echo "FEHLER: SSH_GUEST_SPEC host:port:user" >&2
  exit 1
}
[[ -f "$SSH_KEY" ]] || {
  echo "FEHLER: SSH_KEY $SSH_KEY" >&2
  exit 1
}

SSH_BASE=(ssh -o BatchMode=yes -o ConnectTimeout=12 -o StrictHostKeyChecking=accept-new
  -i "$SSH_KEY" -p "$_port" "$_user@$_host")

echo "=== Warte auf SSH ($_host:$_port) ==="
for _ in $(seq 1 90); do
  if "${SSH_BASE[@]}" "echo ok" >/dev/null 2>&1; then
    break
  fi
  sleep 3
done
"${SSH_BASE[@]}" "echo ok" >/dev/null

echo "=== Repo-Sync ==="
SSH_KEY="$SSH_KEY" SSH_GUEST_SPEC="$SSH_GUEST_SPEC" "$VM_TEST_ROOT/scripts/sync-piinstaller-repo-to-guest.sh"

echo "=== Gast-Autorun ==="
REMOTE_PIINSTALLER_DIR="${REMOTE_PIINSTALLER_DIR:-piinstaller-src}"
"${SSH_BASE[@]}" \
  "VMTEST_SKIP_BACKUP_RESTORE=${VMTEST_SKIP_BACKUP_RESTORE:-0} VMTEST_CONFIRM_AUTORUN=yes VMTEST_PREPARE_BACKUP_DISK=1 VMTEST_BACKUP_DEV=${VMTEST_BACKUP_DEV} VMTEST_CONFIRM_ERASE_DISK=${VMTEST_CONFIRM_ERASE_DISK:-yes} bash \$HOME/${REMOTE_PIINSTALLER_DIR}/tools/vm-test/scripts/in-guest-vmtest-autorun.sh"

echo "OK (Host-Seite)."
