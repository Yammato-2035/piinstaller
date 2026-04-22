#!/usr/bin/env bash
# Im **Gast** als **root** nach der Debian-Installation (oder nach erstem Live-Boot mit sudo).
#
# 1) Deutsche Tastatur (Konsole + X11, soweit localectl verfügbar)
# 2) Delegiert an **in-guest-ensure-ssh-and-login.sh** (openssh-server, Drop-in, authorized_keys)
#
# Aufruf — immer den **echten Pfad** zum Skript angeben (kein „…/“-Platzhalter).
#
# Komfort vom Linux-Host (Sync + Pubkey ohne Datei auf dem Gast + NOPASS, ein sudo-Passwort):
#   ./scripts/host-vmtest-postinstall-nopass.sh
#
# Nach Repo-Sync im Home des Gast-Users (Beispiel volker):
#   sudo VMTEST_ENABLE_NOPASS_SUDO=1 bash /home/volker/piinstaller-src/tools/vm-test/scripts/in-guest-vmtest-postinstall.sh /tmp/id_ed25519.pub volker
#
# Pubkey-Datei muss auf dem Gast existieren. Ohne separate Datei (eine Zeile vom Host pipen):
#   cat id_ed25519.pub | sudo VMTEST_ENABLE_NOPASS_SUDO=1 bash /home/volker/piinstaller-src/tools/vm-test/scripts/in-guest-vmtest-postinstall.sh - volker
#
set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "Bitte mit root ausführen: sudo bash $0 <pubkey-Datei|- > [benutzer …]" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -z "${1:-}" ]]; then
  echo "FEHLER: Erstes Argument fehlt — Pfad zur .pub-Datei auf dem Gast ODER \"-\" wenn der Key per stdin kommt (siehe Kopfkommentar)." >&2
  echo "Beispiel: sudo bash $0 /tmp/id_ed25519.pub volker" >&2
  echo "Beispiel: cat id_ed25519.pub | sudo bash $0 - volker" >&2
  exit 1
fi

if [[ -n "${1:-}" && "$1" != "-" && ! -f "$1" ]]; then
  echo "FEHLER: Public-Key-Datei nicht gefunden: $1" >&2
  echo "Tipp: Datei z. B. nach /tmp kopieren oder Pipe-Variante mit erstem Argument \"-\" (siehe Kopfkommentar)." >&2
  exit 1
fi

if command -v localectl >/dev/null 2>&1; then
  localectl set-keymap de-latin1-nodeadkeys 2>/dev/null || localectl set-keymap de 2>/dev/null || true
  localectl set-x11-keymap de pc105 nodeadkeys 2>/dev/null || localectl set-x11-keymap de pc105 2>/dev/null || true
  localectl status || true
else
  echo "Hinweis: localectl fehlt — Tastatur manuell (dpkg-reconfigure keyboard-configuration)." >&2
fi

# Optional: passwortloses sudo für den VM-Login-User (nur Test-VMs; in Produktion Datei entfernen).
if [[ "${VMTEST_ENABLE_NOPASS_SUDO:-0}" == "1" ]]; then
  VMTEST_LOGIN_USER="${2:-volker}"
  tmp="/tmp/vmtest-nopass-$$.sudoers"
  umask 077
  cat >"$tmp" <<EOF
# Setuphelfer VM-Test — entfernen mit: sudo rm -f /etc/sudoers.d/99-vmtest-setuphelfer
${VMTEST_LOGIN_USER} ALL=(ALL) NOPASSWD: ALL
EOF
  if ! visudo -cf "$tmp" 2>/dev/null; then
    echo "FEHLER: visudo lehnt sudoers-Fragment ab." >&2
    rm -f "$tmp"
    exit 1
  fi
  install -o root -g root -m 0440 "$tmp" /etc/sudoers.d/99-vmtest-setuphelfer
  rm -f "$tmp"
  echo "OK: NOPASSWD für ${VMTEST_LOGIN_USER} → /etc/sudoers.d/99-vmtest-setuphelfer"
fi

exec bash "${SCRIPT_DIR}/in-guest-ensure-ssh-and-login.sh" "$@"
