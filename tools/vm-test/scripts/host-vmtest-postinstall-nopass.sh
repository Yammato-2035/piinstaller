#!/usr/bin/env bash
# Auf dem **Linux-Host**: synct (optional) das Repo, legt NOPASSWD-Sudo an und installiert SSH-Keys
# für den Gast-User — **ohne** eine Public-Key-Datei unter /tmp auf dem Gast.
#
# Der Key kommt per stdin an ``in-guest-vmtest-postinstall.sh - <user>`` (Pipe-Variante).
# Einmalig kann ``sudo`` ein Passwort verlangen: dafür ``-tt`` (Pseudo-TTY).
#
# Beispiel:
#   cd tools/vm-test
#   SSH_KEY=/home/volker/.ssh/id_ed25519_pi SSH_GUEST_SPEC=127.0.0.1:2222:volker \
#     ./scripts/host-vmtest-postinstall-nopass.sh
#
# Public Key: Standard ``\${SSH_KEY}.pub``. Fehlt die Datei, wird der Key aus dem
# Private Key mit ``ssh-keygen -y`` gelesen (keine .pub nötig). Alternativ:
#   SSH_PUB=/pfad/zur/id_ed25519_pi.pub
#
# Ohne Sync (Repo liegt schon unter ~/piinstaller-src):
#   RUN_SYNC=0 SSH_KEY=… SSH_GUEST_SPEC=… ./scripts/host-vmtest-postinstall-nopass.sh
#
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VM_TEST_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_ed25519}"
SSH_KEY="${SSH_KEY/#\~/$HOME}"
SSH_PUB="${SSH_PUB:-}"
[[ -z "$SSH_PUB" ]] || SSH_PUB="${SSH_PUB/#\~/$HOME}"

SSH_GUEST_SPEC="${SSH_GUEST_SPEC:-127.0.0.1:2222:volker}"
REMOTE_DIR_NAME="${REMOTE_PIINSTALLER_DIR:-piinstaller-src}"
RUN_SYNC="${RUN_SYNC:-1}"

IFS=: read -r _host _port _user <<<"$SSH_GUEST_SPEC"
[[ -n "$_port" && -n "$_user" ]] || {
  echo "FEHLER: SSH_GUEST_SPEC muss host:port:user sein" >&2
  exit 1
}
[[ -f "$SSH_KEY" ]] || {
  echo "FEHLER: Private Key fehlt: $SSH_KEY" >&2
  exit 1
}

PUB_LINE=""
if [[ -n "$SSH_PUB" && -f "$SSH_PUB" ]]; then
  PUB_LINE="$(tr -d '\r' <"$SSH_PUB" | head -n1)"
elif [[ -f "${SSH_KEY}.pub" ]]; then
  PUB_LINE="$(tr -d '\r' <"${SSH_KEY}.pub" | head -n1)"
else
  PUB_LINE="$(ssh-keygen -y -f "$SSH_KEY" 2>/dev/null | head -n1 || true)"
fi

if [[ -z "$PUB_LINE" || "$PUB_LINE" != ssh-* ]]; then
  echo "FEHLER: Kein gültiger SSH-Public-Key ermittelbar." >&2
  echo "  Gesucht: SSH_PUB=… oder ${SSH_KEY}.pub oder Ausgabe von: ssh-keygen -y -f $(printf '%q' "$SSH_KEY")" >&2
  exit 1
fi

SSH_BATCH=(ssh -o BatchMode=yes -o ConnectTimeout=15 -o StrictHostKeyChecking=accept-new
  -i "$SSH_KEY" -p "$_port" "$_user@$_host")

if [[ "$RUN_SYNC" == "1" ]]; then
  echo "=== Repo-Sync ==="
  SSH_KEY="$SSH_KEY" SSH_GUEST_SPEC="$SSH_GUEST_SPEC" REMOTE_PIINSTALLER_DIR="$REMOTE_DIR_NAME" \
    "$VM_TEST_ROOT/scripts/sync-piinstaller-repo-to-guest.sh"
fi

POST_REMOTE="$("${SSH_BATCH[@]}" "h=\$(getent passwd \"$_user\" | cut -d: -f6); f=\"\$h/$REMOTE_DIR_NAME/tools/vm-test/scripts/in-guest-vmtest-postinstall.sh\"; test -f \"\$f\" && echo \"\$f\" || true" | tr -d '\r\n')"
[[ -n "$POST_REMOTE" ]] || {
  echo "FEHLER: postinstall-Skript auf dem Gast nicht gefunden (RUN_SYNC=1 oder Pfad prüfen)." >&2
  echo "Erwartet: ~/$REMOTE_DIR_NAME/tools/vm-test/scripts/in-guest-vmtest-postinstall.sh" >&2
  exit 1
}

echo "=== Postinstall + NOPASS (Pubkey per base64, kein /tmp auf dem Gast) → $POST_REMOTE ==="
echo "Hinweis: Bei Passwort-Prompt für sudo einmal das Passwort für $_user eingeben."
# Kein „ssh < pubkey“: sonst kollidiert stdin mit dem TTY für sudo.
PB64="$(printf '%s' "$PUB_LINE" | base64 | tr -d '\n')"
ssh -tt -o ConnectTimeout=20 -o StrictHostKeyChecking=accept-new \
  -i "$SSH_KEY" -p "$_port" "$_user@$_host" \
  "echo $(printf '%q' "$PB64") | base64 -d | sudo env VMTEST_ENABLE_NOPASS_SUDO=1 bash $(printf '%q' "$POST_REMOTE") - $(printf '%q' "$_user")"

echo "OK. Test: ssh -o BatchMode=yes -i $SSH_KEY -p $_port $_user@$_host 'sudo -n true && echo NOPASSWD-ok'"
