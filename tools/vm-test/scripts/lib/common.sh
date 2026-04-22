#!/usr/bin/env bash
# Gemeinsame Sicherheits- und Pfadlogik für VM-Testskripte.
# Keine Ausführung gegen Host-Root oder außerhalb von VM_TEST_ROOT/disks.

set -euo pipefail

# Repo-Root: tools/vm-test/scripts/lib -> ../../../
_VM_TEST_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VM_TEST_ROOT="$(cd "${_VM_TEST_SCRIPT_DIR}/../.." && pwd)"
VM_TEST_DISKS="${VM_TEST_DISKS:-${VM_TEST_ROOT}/disks}"

die() { echo "FEHLER: $*" >&2; exit 1; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Befehl fehlt (nicht installieren von hier): $1"
}

# Nur Dateien unter VM_TEST_DISKS (Basisname oder relativer Name ohne ..).
resolve_disk_path() {
  local name="$1"
  [[ "$name" != *".."* ]] || die "Pfad enthält '..': $name"
  mkdir -p "$VM_TEST_DISKS"
  local base
  base="$(cd "$VM_TEST_DISKS" && pwd)"
  local full
  full="$(realpath -m "${base}/${name}")" || die "realpath fehlgeschlagen: $name"
  [[ "$full" == "$base"/* ]] || die "Pfad liegt nicht unter VM_TEST_DISKS ($base): $full"
  [[ -e "$full" ]] || die "Datei existiert nicht: $full"
  echo "$full"
}

assert_disk_extension() {
  local f="$1"
  case "$f" in
    *.vdi|*.qcow2|*.img) ;;
    *) die "Nur Test-Images mit Endung .vdi, .qcow2 oder .img erlaubt: $f" ;;
  esac
}

list_test_disks() {
  echo "Konfiguriertes VM_TEST_DISKS: $VM_TEST_DISKS"
  ls -la "$VM_TEST_DISKS" 2>/dev/null || echo "(leer oder nicht angelegt)"
}
