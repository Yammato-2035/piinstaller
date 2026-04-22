#!/usr/bin/env bash
# STRICT (Full-Recovery): Zerstört ausschließlich tools/vm-test/disks/system.vdi
# nach explizitem Flag und Bestätigung "yes". Keine anderen Dateinamen.
#
# Aufruf: ./05-destroy-testdisk-safe.sh system.vdi DESTROY_TEST_DISK
#
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

STRICT_NAME="system.vdi"
basename_only="${1:-}"
confirm="${2:-}"

[[ -n "$basename_only" ]] || die "Usage: $0 system.vdi DESTROY_TEST_DISK"
[[ "$confirm" == "DESTROY_TEST_DISK" ]] || die "Zweites Argument muss exakt DESTROY_TEST_DISK sein"
[[ "$basename_only" == "$STRICT_NAME" ]] || die "Strict-Modus: nur Basisname '$STRICT_NAME' erlaubt, nicht: $basename_only"

CANON_DISKS="$(realpath "${VM_TEST_ROOT}/disks")"
CURRENT_DISKS="$(cd "$VM_TEST_DISKS" && pwd)"
[[ "$CURRENT_DISKS" == "$CANON_DISKS" ]] || die "Strict-Modus: VM_TEST_DISKS muss exakt ${VM_TEST_ROOT}/disks sein (kanonisch: $CANON_DISKS), ist: $CURRENT_DISKS"

full="$(resolve_disk_path "$STRICT_NAME")"
assert_disk_extension "$full"

[[ "$(basename "$full")" == "$STRICT_NAME" ]] || die "Zieldatei muss exakt $STRICT_NAME heißen: $full"
[[ "$full" == "$CANON_DISKS/$STRICT_NAME" ]] || die "Abbruch: Aufgelöster Pfad liegt nicht exakt unter $CANON_DISKS/$STRICT_NAME: $full"

cat >&2 <<EOF

╔══════════════════════════════════════════════════════════════════╗
║  WARNUNG: DESTRUKTIVE AKTION (nur diese eine Datei)              ║
║  Ziel: $full
║  Es werden KEINE Host-Platten (/dev/sd*) angesprochen.           ║
║  VM mit dieser Systemplatte muss aus sein; Medium ggf. trennen.  ║
╚══════════════════════════════════════════════════════════════════╝

EOF
echo "Ziel zur Zerstörung (Allowlist + Pfadprüfung OK):"
ls -la "$full"
echo ""
read -r -p "Wirklich zerstören? Tippe exakt yes zum Fortfahren: " ans
[[ "${ans:-}" == "yes" ]] || die "Abgebrochen."

if command -v shred >/dev/null 2>&1; then
  shred -n 1 -z -u "$full" || die "shred fehlgeschlagen"
else
  rm -f "$full" || die "rm fehlgeschlagen"
fi

echo "Erledigt: $full entfernt oder zerstört."
