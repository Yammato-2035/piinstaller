#!/usr/bin/env bash
# Auf dem **Linux-Host** ausführen (nicht im Gast).
# Wendet per SSH das Gast-Skript ``in-guest-ensure-ssh-and-login.sh`` auf eine oder
# mehrere Test-VMs an (Standard: setuphelfer-a:2222, setuphelfer-b:2223, Benutzer ``user``).
#
# Voraussetzung: Mindestens **ein** funktionierender SSH-Zugang (Passwort oder bereits Key),
# damit ``ssh`` und ``sudo`` auf dem Gast laufen. Wenn SSH komplett hängt: siehe SSH_UND_LOGIN.md
# (tty-Konsole oder Rescue-ISO, Skript dort als root ausführen).
#
# Nutzung:
#   cd tools/vm-test
#   ./scripts/host-ssh-fix-vm-test-vms.sh
#   SSH_KEY=~/.ssh/id_ed25519 VM_SSH_TARGETS="127.0.0.1:2222:volker 127.0.0.1:2223:volker" ./scripts/host-ssh-fix-vm-test-vms.sh
#
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GUEST_SCRIPT="${SCRIPT_DIR}/in-guest-ensure-ssh-and-login.sh"

SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_ed25519}"
PUB="${SSH_KEY}.pub"
[[ -f "$PUB" ]] || { echo "FEHLER: Public Key fehlt: $PUB (oder SSH_KEY setzen)" >&2; exit 1; }
[[ -f "$GUEST_SCRIPT" ]] || { echo "FEHLER: $GUEST_SCRIPT fehlt" >&2; exit 1; }

# host:port:user …
TARGETS="${VM_SSH_TARGETS:-127.0.0.1:2222:volker 127.0.0.1:2223:volker}"

run_one() {
  local spec="$1"
  local host port user
  IFS=: read -r host port user <<<"$spec"
  [[ -n "$port" && -n "$user" ]] || { echo "FEHLER: Ziel ungültig (host:port:user): $spec" >&2; return 1; }
  echo "=== $host Port $port Benutzer $user ==="
  if ! ssh -o BatchMode=yes -o ConnectTimeout=12 -o StrictHostKeyChecking=accept-new \
    -i "$SSH_KEY" -p "$port" "$user@$host" "sudo -n true" 2>/dev/null; then
    echo "Hinweis: sudo -n nicht möglich — interaktives sudo-Passwort kann nötig sein."
  fi
  # Skript + Pubkey auf den Gast kopieren und ausführen (ein sudo-Prompt möglich)
  scp -o BatchMode=yes -o ConnectTimeout=12 -o StrictHostKeyChecking=accept-new \
    -i "$SSH_KEY" -P "$port" "$GUEST_SCRIPT" "$PUB" "$user@$host:/tmp/" >/dev/null
  ssh -o ConnectTimeout=12 -o StrictHostKeyChecking=accept-new \
    -i "$SSH_KEY" -p "$port" "$user@$host" \
    "sudo bash /tmp/in-guest-ensure-ssh-and-login.sh /tmp/$(basename "$PUB") $user"
}

for spec in $TARGETS; do
  [[ -n "${spec// }" ]] || continue
  run_one "$spec" || echo "FEHLER bei $spec (siehe Meldung oben)" >&2
done

echo "Fertig. Test: ssh -p 2222 -i $SSH_KEY volker@127.0.0.1 true"
