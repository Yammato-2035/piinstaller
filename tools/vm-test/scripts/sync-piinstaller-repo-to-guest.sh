#!/usr/bin/env bash
# Auf dem **Linux-Host** ausführen: spiegelt das Piinstaller-Repository per SSH-Tarstream
# ins Gast-Home (Standard: ~/piinstaller-src). Nutzt das Root-Dateisystem des Gastes,
# nicht /tmp (tmpfs), und schließt große Host-Artefakte aus (VM-Disks, Tauri-target, …).
#
# Voraussetzung: SSH-Key-Login (BatchMode), z. B. nach host-ssh-fix-vm-test-vms.sh.
#
# Beispiel:
#   cd tools/vm-test
#   SSH_KEY=~/.ssh/id_ed25519_pi SSH_GUEST_SPEC=127.0.0.1:2222:volker ./scripts/sync-piinstaller-repo-to-guest.sh
#
# System-Installation braucht danach einmal interaktives sudo auf dem Gast, z. B.:
#   ssh -t -i ~/.ssh/id_ed25519_pi -p 2222 volker@127.0.0.1 \
#     'cd ~/piinstaller-src && sudo env PI_INSTALLER_USER=volker bash scripts/install-system.sh && sudo bash tools/vm-test/scripts/in-guest-setup.sh'
#
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
[[ -f "$REPO_ROOT/scripts/install-system.sh" ]] || {
  echo "FEHLER: Repository-Root scheint falsch: $REPO_ROOT" >&2
  exit 1
}

SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_ed25519}"
SSH_GUEST_SPEC="${SSH_GUEST_SPEC:-127.0.0.1:2222:volker}"
REMOTE_DIR_NAME="${REMOTE_PIINSTALLER_DIR:-piinstaller-src}"

IFS=: read -r SSH_HOST SSH_PORT SSH_USER <<<"$SSH_GUEST_SPEC"
[[ -n "$SSH_PORT" && -n "$SSH_USER" ]] || {
  echo "FEHLER: SSH_GUEST_SPEC muss host:port:user sein, z. B. 127.0.0.1:2222:volker" >&2
  exit 1
}
[[ -f "$SSH_KEY" ]] || { echo "FEHLER: Private Key fehlt: $SSH_KEY" >&2; exit 1; }

SSH_BASE=(ssh -o BatchMode=yes -o ConnectTimeout=15 -o StrictHostKeyChecking=accept-new
  -i "$SSH_KEY" -p "$SSH_PORT" "$SSH_USER@$SSH_HOST")

echo "=== Sync $REPO_ROOT -> $SSH_USER@$SSH_HOST:$SSH_PORT ~/ $REMOTE_DIR_NAME ==="

"${SSH_BASE[@]}" "rm -rf \"\$HOME/$REMOTE_DIR_NAME\" && mkdir -p \"\$HOME/$REMOTE_DIR_NAME\""

(
  cd "$REPO_ROOT"
  tar cf - \
    --exclude=.git \
    --exclude=frontend/node_modules \
    --exclude=node_modules \
    --exclude=.venv \
    --exclude='**/__pycache__' \
    --exclude='**/*.pyc' \
    --exclude=tools/vm-test/disks \
    --exclude=tools/vm-test/reports \
    --exclude=frontend/src-tauri/target \
    .
) | "${SSH_BASE[@]}" "tar xf - -C \"\$HOME/$REMOTE_DIR_NAME\""

"${SSH_BASE[@]}" "du -sh \"\$HOME/$REMOTE_DIR_NAME\" && test -f \"\$HOME/$REMOTE_DIR_NAME/scripts/install-system.sh\""
echo OK
echo "Gast-Pfade (Beispiel): Postinstall → ~/${REMOTE_DIR_NAME}/tools/vm-test/scripts/in-guest-vmtest-postinstall.sh"
echo "Pfad prüfen auf dem Gast: bash ~/${REMOTE_DIR_NAME}/tools/vm-test/scripts/in-guest-which-vmtest-script.sh"
