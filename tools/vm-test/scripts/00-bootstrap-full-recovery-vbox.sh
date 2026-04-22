#!/usr/bin/env bash
# Orchestrierung: Ist-Prüfung, VDI-Erzeugung, VM-Definition (VirtualBox).
# Schreibt nur unter tools/vm-test/ (Logs, disks). Keine Host-Paketinstallation.
# Keine Zerstörung, kein Gast-Zugriff.
#
# Aufruf aus tools/vm-test/:
#   ./scripts/00-bootstrap-full-recovery-vbox.sh
#
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VM_TEST_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

LOG_DIR="${VM_TEST_ROOT}/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/bootstrap-$(date +%Y%m%d-%H%M%S).log"

log() {
  local line="[$(date -Iseconds)] $*"
  echo "$line" | tee -a "$LOG_FILE"
}

log "=== Full-Recovery VBox Bootstrap ==="
log "VM_TEST_ROOT=$VM_TEST_ROOT"
log "Logdatei: $LOG_FILE"

# --- Phase 1: Ist-Prüfung ---
require_cmd VBoxManage

for need in \
  "${SCRIPT_DIR}/01-create-disks-vbox.sh" \
  "${SCRIPT_DIR}/02-vbox-define-vm.sh"; do
  [[ -f "$need" ]] || die "Pflichtdatei fehlt: $need"
done
log "Phase 1 OK: VBoxManage und Basisskripte vorhanden."

# --- Phase 2: Disks ---
log "Phase 2: 01-create-disks-vbox.sh"
( cd "$SCRIPT_DIR" && ./01-create-disks-vbox.sh ) 2>&1 | tee -a "$LOG_FILE"

DISK_SYS="${VM_TEST_DISKS}/system.vdi"
DISK_BACK="${VM_TEST_DISKS}/backup.vdi"
DISK_REST="${VM_TEST_DISKS}/restore-target.vdi"
for f in "$DISK_SYS" "$DISK_BACK" "$DISK_REST"; do
  [[ -f "$f" ]] || die "Erwartete Datei fehlt: $f"
done

# Dynamische VDI: Dateigröße auf dem Host ist klein — logische Kapazität per VBox prüfen
cap_line="$(VBoxManage showmediuminfo disk "$DISK_SYS" 2>/dev/null | grep -i '^Capacity:' || true)"
cap_mb="$(echo "$cap_line" | awk '{print $2}')"
unit="$(echo "$cap_line" | awk '{print $3}')"
[[ -n "$cap_mb" ]] || die "Konnte VDI-Kapazität nicht lesen: $DISK_SYS (VBoxManage showmediuminfo disk)"
[[ "${unit,,}" == mbytes* ]] || die "Unerwartete Kapazitätszeile (erwartet MBytes): $cap_line"
MIN_SYS_MB=1024
[[ "$cap_mb" -ge "$MIN_SYS_MB" ]] || die "system.vdi logische Kapazität zu klein: ${cap_mb} MiB (min ${MIN_SYS_MB} MiB)"
log "Phase 2 OK: system.vdi Kapazität ${cap_mb} MiB (≥ 1 GiB), alle drei VDI vorhanden."

# --- Phase 3: VM definieren ---
log "Phase 3: 02-vbox-define-vm.sh"
( cd "$SCRIPT_DIR" && ./02-vbox-define-vm.sh ) 2>&1 | tee -a "$LOG_FILE"

VM_NAME="${VM_NAME:-setuphelfer-recovery-test}"
if VBoxManage list vms | grep -qF "\"${VM_NAME}\""; then
  log "Phase 3 OK: VM in VBox registriert: ${VM_NAME}"
else
  die "VM nicht gefunden in VBoxManage list vms: ${VM_NAME}"
fi

log "Bootstrap abgeschlossen. Nächste Schritte: INSTALL_GUIDE.md, dann Gast-Setup, BACKUP_RUNBOOK.md."
log "Diagnose optional: ./scripts/09-collect-diagnostics.sh"
