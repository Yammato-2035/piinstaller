#!/usr/bin/env bash
# Im **Gast** ausführen (root): isolierter Restore-Test nach VM_FRESH_INSTALL_AND_BACKUP.md Phase 6.
# Entpackt ein Full-Backup-Archiv nur nach /tmp/setuphelfer-restore-test — kein Schreiben auf /.
#
# Voraussetzungen:
#   - Backup-Medium gemountet (z. B. /mnt/backup-test), darin mindestens ein pi-backup-full-*.tar.gz
#   - Setuphelfer unter /opt/setuphelfer mit Backend-venv (install-system.sh)
#
# Aufruf:
#   sudo bash tools/vm-test/scripts/in-guest-restore-isolated-step.sh
# Optional:
#   sudo env BACKUP_DIR=/mnt/backup-test BACKUP_ARCHIVE=/pfad/zum/archiv.tar.gz \
#     bash tools/vm-test/scripts/in-guest-restore-isolated-step.sh
#
set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "Bitte mit root-Rechten ausführen: sudo bash $0" >&2
  exit 1
fi

INSTALL_ROOT="${SETUPHELFER_INSTALL:-/opt/setuphelfer}"
BACKEND_DIR="${INSTALL_ROOT}/backend"
PYTHON="${BACKEND_DIR}/venv/bin/python3"
BACKUP_DIR="${BACKUP_DIR:-/mnt/backup-test}"
RESTORE_DIR="${RESTORE_DIR:-/tmp/setuphelfer-restore-test}"

if [[ ! -x "$PYTHON" ]]; then
  echo "FEHLER: Backend-Python fehlt: $PYTHON (Setuphelfer installiert?)" >&2
  exit 1
fi

if [[ ! -d "$BACKUP_DIR" ]]; then
  echo "FEHLER: Backup-Verzeichnis fehlt: $BACKUP_DIR" >&2
  echo "Hinweis: Marker/Mount-Punkt: sudo bash tools/vm-test/scripts/in-guest-setup.sh; dann Platte nach $BACKUP_DIR mounten (BACKUP_RUNBOOK.md)." >&2
  exit 1
fi

# Versehentlich gesetztes BACKUP_ARCHIVE (z. B. aus der Shell-Umgebung) ignorieren, wenn keine .tar.gz-Datei.
if [[ -n "${BACKUP_ARCHIVE:-}" ]]; then
  if [[ ! "$BACKUP_ARCHIVE" =~ \.(tar\.gz|tgz)$ ]] || [[ ! -f "$BACKUP_ARCHIVE" ]]; then
    echo "WARN: BACKUP_ARCHIVE ist kein gültiges Archiv ($(printf '%q' "$BACKUP_ARCHIVE")) — wird ignoriert." >&2
    unset BACKUP_ARCHIVE
  fi
fi

if [[ -n "${BACKUP_ARCHIVE:-}" ]]; then
  ARCHIVE="$BACKUP_ARCHIVE"
  if [[ ! -f "$ARCHIVE" ]]; then
    echo "FEHLER: BACKUP_ARCHIVE ist keine Datei: $ARCHIVE" >&2
    exit 1
  fi
else
  shopt -s nullglob
  mapfile -t _cands < <(ls -t "$BACKUP_DIR"/pi-backup-full-*.tar.gz 2>/dev/null || true)
  shopt -u nullglob
  if [[ ${#_cands[@]} -eq 0 ]]; then
    echo "FEHLER: Kein pi-backup-full-*.tar.gz unter $BACKUP_DIR gefunden." >&2
    exit 1
  fi
  ARCHIVE="${_cands[0]}"
  if [[ ${#_cands[@]} -gt 1 ]]; then
    echo "Hinweis: mehrere Archive — neuestes gewählt: $ARCHIVE" >&2
  fi
fi

echo "=== Isolierter Restore-Test ==="
echo "Archiv:    $ARCHIVE"
echo "Ziel:      $RESTORE_DIR"
echo "Python:    $PYTHON"
echo ""

rm -rf "$RESTORE_DIR"
mkdir -p "$RESTORE_DIR"

if [[ -n "${SUDO_USER:-}" && "$SUDO_USER" != root ]]; then
  chown -R "${SUDO_USER}:${SUDO_USER}" "$RESTORE_DIR"
fi

ARCHIVE_ABS="$(readlink -f "$ARCHIVE")"
RESTORE_ABS="$(readlink -f "$RESTORE_DIR")"

(
  cd "$BACKEND_DIR"
  if [[ -n "${SUDO_USER:-}" && "$SUDO_USER" != root ]]; then
    sudo -u "$SUDO_USER" -H "$PYTHON" -c "
from pathlib import Path
from modules.restore_engine import restore_files
arch = Path('${ARCHIVE_ABS}')
td = Path('${RESTORE_ABS}').resolve()
print(restore_files(arch, td, allowed_target_prefixes=(td,)))
"
  else
    "$PYTHON" -c "
from pathlib import Path
from modules.restore_engine import restore_files
arch = Path('${ARCHIVE_ABS}')
td = Path('${RESTORE_ABS}').resolve()
print(restore_files(arch, td, allowed_target_prefixes=(td,)))
"
  fi
)

echo ""
echo "=== Kurzprüfung (Dateien unter Ziel) ==="
find "$RESTORE_DIR" -maxdepth 4 -type f 2>/dev/null | head -40 || true
echo ""
echo "Optional: Marker-Pfade im Zielbaum prüfen, z. B.:"
echo "  find $RESTORE_DIR -path '*/opt/setuphelfer-test/*' -print"
echo "Fertig."
