#!/usr/bin/env bash
# Im **Gast** als normaler User mit **sudo -n** (NOPASSWD): Kette für VM-Tests —
# Marker/Mount-Punkt, optional Backup-Platte, install-system nicht-interaktiv,
# Full-Backup (async) + isolierter Restore unter /tmp.
#
# Einmalig NOPASSWD einrichten (nur Test-VM):
#   sudo VMTEST_ENABLE_NOPASS_SUDO=1 bash …/in-guest-vmtest-postinstall.sh /tmp/id.pub volker
#
# Dann z. B.:
#   VMTEST_CONFIRM_AUTORUN=yes VMTEST_PREPARE_BACKUP_DISK=1 VMTEST_BACKUP_DEV=/dev/sdc \
#     bash ~/piinstaller-src/tools/vm-test/scripts/in-guest-vmtest-autorun.sh
#
# Ohne Backup/Restore (nur Installation):
#   VMTEST_CONFIRM_AUTORUN=yes VMTEST_SKIP_BACKUP_RESTORE=1 bash …/in-guest-vmtest-autorun.sh
#
set -euo pipefail

[[ "${VMTEST_CONFIRM_AUTORUN:-}" == "yes" ]] || {
  echo "FEHLER: Zur Absicherung VMTEST_CONFIRM_AUTORUN=yes setzen." >&2
  exit 2
}

REPO="${VMTEST_REPO_DIR:-$HOME/piinstaller-src}"
[[ -d "$REPO" ]] || {
  echo "FEHLER: Repository-Verzeichnis fehlt: $REPO (sync vom Host?)" >&2
  exit 1
}

sudo -n true || {
  echo "FEHLER: sudo -n schlägt fehl — VMTEST_ENABLE_NOPASS_SUDO=1 bei Postinstall setzen oder sudoers anpassen." >&2
  exit 2
}

PIU="${VMTEST_PI_USER:-${SUDO_USER:-$USER}}"
export PI_INSTALLER_USER="$PIU"

echo "=== [1/5] in-guest-setup ==="
sudo -n bash "$REPO/tools/vm-test/scripts/in-guest-setup.sh"

if [[ "${VMTEST_PREPARE_BACKUP_DISK:-0}" == "1" ]]; then
  echo "=== [2/5] Backup-Platte ==="
  : "${VMTEST_BACKUP_DEV:?VMTEST_BACKUP_DEV setzen (z. B. /dev/sdc)}"
  sudo -n env VMTEST_BACKUP_DEV="$VMTEST_BACKUP_DEV" \
    VMTEST_CONFIRM_ERASE_DISK="${VMTEST_CONFIRM_ERASE_DISK:-yes}" \
    VMTEST_BACKUP_MOUNT="${VMTEST_BACKUP_MOUNT:-/mnt/backup-test}" \
    bash "$REPO/tools/vm-test/scripts/in-guest-prepare-backup-disk.sh"
else
  echo "=== [2/5] Backup-Platte übersprungen (VMTEST_PREPARE_BACKUP_DISK!=1) ==="
fi

echo "=== [3/5] install-system (noninteractive) ==="
sudo -n env SETUPHELFER_NONINTERACTIVE=1 \
  SETUPHELFER_SYSTEMD_ENABLE="${SETUPHELFER_SYSTEMD_ENABLE:-yes}" \
  SETUPHELFER_SYSTEMD_START_NOW="${SETUPHELFER_SYSTEMD_START_NOW:-yes}" \
  PI_INSTALLER_USER="$PIU" \
  bash "$REPO/scripts/install-system.sh"

if [[ "${VMTEST_SKIP_BACKUP_RESTORE:-0}" == "1" ]]; then
  echo "=== Backup/Restore übersprungen (VMTEST_SKIP_BACKUP_RESTORE=1) — fertig. ==="
  exit 0
fi

export VMTEST_API_BASE="${VMTEST_API_BASE:-http://127.0.0.1:8000}"
export VMTEST_BACKUP_DIR="${VMTEST_BACKUP_DIR:-/mnt/backup-test}"
export VMTEST_BACKUP_POLL_MAX_SEC="${VMTEST_BACKUP_POLL_MAX_SEC:-14400}"

echo "=== [4/5] Warte API + Full-Backup (async) ==="
for _ in $(seq 1 90); do
  if curl -sf "${VMTEST_API_BASE}/api/version" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
if ! curl -sf "${VMTEST_API_BASE}/api/version" >/dev/null 2>&1; then
  echo "FEHLER: Backend unter ${VMTEST_API_BASE} nicht erreichbar." >&2
  exit 1
fi

python3 <<'PY'
import json, os, time, urllib.request

api = os.environ["VMTEST_API_BASE"].rstrip("/")
backup_dir = os.environ["VMTEST_BACKUP_DIR"]
max_sec = int(os.environ.get("VMTEST_BACKUP_POLL_MAX_SEC", "14400"))


def open_url(method, path, data=None, timeout=120):
    url = api + path
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        r = urllib.request.Request(url, data=body, method=method)
        r.add_header("Content-Type", "application/json")
    else:
        r = urllib.request.Request(url, method=method)
    return urllib.request.urlopen(r, timeout=timeout)

def jload(resp):
    return json.loads(resp.read().decode("utf-8"))

with open_url("POST", "/api/backup/create", {"type": "full", "backup_dir": backup_dir, "target": "local", "async": True}) as resp:
    out = jload(resp)

job_id = out.get("job_id") or (out.get("details") or {}).get("job_id")
if not job_id:
    raise SystemExit(f"Kein job_id in API-Antwort: {out!r}")

print("job_id:", job_id)
deadline = time.time() + max_sec
last = ""
while time.time() < deadline:
    with open_url("GET", f"/api/backup/jobs/{job_id}") as resp:
        data = jload(resp)
    job = data.get("job") or {}
    st = job.get("status") or ""
    if st != last:
        print("status:", st)
        last = st
    if st in ("success", "error", "cancelled"):
        if st != "success":
            raise SystemExit(f"Backup fehlgeschlagen: {data!r}")
        print("Backup OK")
        break
    time.sleep(5)
else:
    raise SystemExit("Timeout beim Warten auf Backup-Job")
PY

echo "=== [5/5] isolierter Restore-Test ==="
sudo -n env BACKUP_DIR="${VMTEST_BACKUP_DIR:-/mnt/backup-test}" \
  bash "$REPO/tools/vm-test/scripts/in-guest-restore-isolated-step.sh"

echo "=== VM-Autorun abgeschlossen ==="
