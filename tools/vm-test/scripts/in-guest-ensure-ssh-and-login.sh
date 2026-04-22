#!/usr/bin/env bash
# Im **Gast** als **root** ausführen (Konsole tty, Rescue-chroot oder „sudo bash“).
#
# Richtet openssh-server, eine klare sshd-Drop-in-Config und SSH-Public-Keys für
# einen oder mehrere Benutzer ein. Behebt typische Ursachen für „GUI-Login geht nicht“
# / „SSH hängt am Banner“ nur soweit sie sshd/Shell/Home betreffen (kein Display-Manager-Tuning).
#
# Nutzung:
#   sudo bash in-guest-ensure-ssh-and-login.sh /pfad/zur/id_ed25519.pub user
#   cat host-id_ed25519.pub | sudo bash in-guest-ensure-ssh-and-login.sh - volker
#
set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "Bitte als root ausführen: sudo bash $0 …" >&2
  exit 1
fi

PUBKEY_LINE=""
if [[ "${1:-}" == "-" ]]; then
  shift
  IFS= read -r PUBKEY_LINE || true
elif [[ -n "${1:-}" && -f "$1" ]]; then
  PUBFILE="$1"
  shift
  PUBKEY_LINE="$(tr -d '\r' <"$PUBFILE" | head -n1)"
else
  echo "Aufruf: sudo bash $0 <id_ed25519.pub> [benutzer …]" >&2
  echo "   oder: cat id_ed25519.pub | sudo bash $0 - [benutzer …]" >&2
  exit 1
fi

if [[ -z "$PUBKEY_LINE" ]]; then
  echo "FEHLER: Leerer Public Key." >&2
  exit 1
fi

[[ "$PUBKEY_LINE" == ssh-* ]] || { echo "FEHLER: Pubkey muss mit ssh-rsa / ssh-ed25519 / ecdsa beginnen." >&2; exit 1; }

TARGET_USERS=("$@")
if [[ ${#TARGET_USERS[@]} -eq 0 ]]; then
  TARGET_USERS=(volker)
fi

export DEBIAN_FRONTEND=noninteractive
if command -v apt-get >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y --no-install-recommends openssh-server sudo >/dev/null
fi

install -d -m0755 /etc/ssh/sshd_config.d
cat >/etc/ssh/sshd_config.d/70-setuphelfer-vmtest.conf <<'CFG'
# Setuphelfer VM-Test (nur Test-VMs) — explizit Pubkey + Passwort, damit Erstzugriff und Keys funktionieren.
# Nach verifiziertem Key-Login: PasswordAuthentication auf „no“ setzen und „systemctl reload ssh“.
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys .ssh/authorized_keys2
PasswordAuthentication yes
KbdInteractiveAuthentication yes
CFG

# Defekte / leere Drop-ins von früheren Experimenten vermeiden (nur unsere Datei ist maßgeblich für diese Werte).
if [[ -f /etc/ssh/sshd_config.d/60-setuphelfer-vmtest.conf ]]; then
  rm -f /etc/ssh/sshd_config.d/60-setuphelfer-vmtest.conf
fi

for u in "${TARGET_USERS[@]}"; do
  UHOME="$(getent passwd "$u" | cut -d: -f6)"
  if [[ -z "$UHOME" || ! -d "$UHOME" ]]; then
    echo "WARNUNG: Benutzer $u existiert nicht oder ohne Home — übersprungen." >&2
    continue
  fi
  install -d -m0700 -o "$u" -g "$u" "$UHOME/.ssh"
  AUTH="$UHOME/.ssh/authorized_keys"
  touch "$AUTH"
  chown "$u:$u" "$AUTH"
  chmod 0600 "$AUTH"
  if ! grep -qxF "$PUBKEY_LINE" "$AUTH" 2>/dev/null; then
    printf '%s\n' "$PUBKEY_LINE" >>"$AUTH"
    chown "$u:$u" "$AUTH"
    chmod 0600 "$AUTH"
  fi
  # Häufige Login-Probleme: gesperrtes Konto oder falsche Shell
  if command -v passwd >/dev/null 2>&1; then
    passwd -u "$u" 2>/dev/null || true
  fi
  if getent passwd "$u" | cut -d: -f7 | grep -q '^/usr/sbin/nologin\|^/bin/false$'; then
    chsh -s /bin/bash "$u" || true
  fi
done

systemctl enable ssh 2>/dev/null || systemctl enable sshd 2>/dev/null || true
if ! sshd -t 2>/tmp/setuphelfer-sshd-t.err; then
  echo "FEHLER: sshd -t schlägt fehl:" >&2
  cat /tmp/setuphelfer-sshd-t.err >&2 || true
  exit 1
fi
systemctl restart ssh 2>/dev/null || systemctl restart sshd 2>/dev/null || true

echo "OK: openssh-server aktiv, Drop-in /etc/ssh/sshd_config.d/70-setuphelfer-vmtest.conf, Keys für: ${TARGET_USERS[*]}"
echo "Test vom Host: ssh -p <NAT-Port> -i <passender_private_key> ${TARGET_USERS[0]}@127.0.0.1"
