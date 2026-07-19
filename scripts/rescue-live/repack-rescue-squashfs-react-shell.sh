#!/usr/bin/env bash
# Repack existing rescue squashfs with React shell payload (no lb build, no apt).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PROJECT_VERSION="${SETUPHELFER_REPACK_VERSION:-$(python3 -c "import json; from pathlib import Path; root=Path('${REPO_ROOT}'); payload=root/'config/rescue_payload_version.json'; print(json.loads(payload.read_text(encoding='utf-8')).get('rescue_payload_version') if payload.is_file() else json.loads((root/'config/version.json').read_text(encoding='utf-8')).get('project_version','1.7.10.1'))")}"
OUT_SQ="${REPO_ROOT}/build/rescue/filesystem.squashfs.repacked-${PROJECT_VERSION}"

resolve_repack_source_squashfs() {
  python3 - "$1" "$2" <<'PY'
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
out_name = f"filesystem.squashfs.repacked-{sys.argv[2]}"
candidates = [p for p in root.glob("filesystem.squashfs.repacked-*") if p.name != out_name]
order = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)

def has_chromium(path: Path) -> bool:
    proc = subprocess.run(
        ["unsquashfs", "-ll", str(path)],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    blob = (proc.stdout or "") + (proc.stderr or "")
    return "usr/bin/chromium" in blob

for path in order:
    if has_chromium(path):
        print(path)
        raise SystemExit(0)
raise SystemExit(1)
PY
}

if [[ -n "${1:-}" ]]; then
  SOURCE_SQ="$1"
else
  SOURCE_SQ="$(resolve_repack_source_squashfs "$REPO_ROOT/build/rescue" "$PROJECT_VERSION")" \
    || die "no repack source squashfs with usr/bin/chromium found under build/rescue/" 21
fi
SUMMARY="${REPO_ROOT}/docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json"

die() { echo "ERROR: $*" >&2; exit "${2:-1}"; }

[[ -f "$SOURCE_SQ" ]] || die "source squashfs missing: $SOURCE_SQ" 22
command -v unsquashfs >/dev/null || die "unsquashfs missing" 23
command -v mksquashfs >/dev/null || die "mksquashfs missing" 24

"${REPO_ROOT}/scripts/check-rescue-ui-smoke-gate.sh" || die "rescue UI smoke gate failed — payload build forbidden" 26

"${REPO_ROOT}/scripts/rescue-live/build-rescue-react-ui.sh"
UI_SRC="${REPO_ROOT}/build/rescue/ui"
python3 - <<PY
import json
from pathlib import Path
manifest_path = Path(${UI_SRC@Q}) / "rescue-ui-manifest.json"
if manifest_path.is_file():
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["version"] = ${PROJECT_VERSION@Q}
    manifest_path.write_text(json.dumps(data, indent=2) + "\\n", encoding="utf-8")
PY

WORKDIR="$(mktemp -d)"
ROOT="${WORKDIR}/root"
trap 'rm -rf "$WORKDIR"' EXIT

unsquashfs -force -no-xattrs -d "$ROOT" "$SOURCE_SQ" >/dev/null

[[ -f "${UI_SRC}/rescue.html" ]] || die "React UI build missing" 25

mkdir -p "${ROOT}/usr/share/setuphelfer/rescue/ui"
cp -a "${UI_SRC}/." "${ROOT}/usr/share/setuphelfer/rescue/ui/"

IMAGE="${REPO_ROOT}/scripts/rescue-live/image"
for script in \
  setuphelfer-rescue-common.sh \
  setuphelfer-rescue-ui-launch \
  setuphelfer-rescue-kiosk-start \
  setuphelfer-rescue-backend-start.sh \
  setuphelfer-rescue-gui-start.sh \
  setuphelfer-rescue-state-write \
  setuphelfer-rescue-evidence-spool-sync \
  setuphelfer-rescue-start-assistant \
  setuphelfer-rescue-network-onboarding \
  setuphelfer-rescue-telemetry-push \
  setuphelfer-rescue-media-check \
  setuphelfer-rescue-disk-discovery \
  setuphelfer-rescue-boot-diagnostics \
  setuphelfer-rescue-boot-evidence-init \
  setuphelfer-rescue-boot-progress \
  setuphelfer-rescue-auto-msi-evidence \
  setuphelfer-rescue-auto-physical-e2e \
  setuphelfer-rescue-auto-discovery \
  setuphelfer-rescue-auto-discovery-start-gate \
  setuphelfer-rescue-auto-discovery-runner \
  setuphelfer-rescue-boot-observer \
  setuphelfer-rescue-resolve-setup-logs \
  setuphelfer-rescue-late-journal-harvest \
  setuphelfer-rescue-boot-finalizer \
  setuphelfer-rescue-tui-guard \
  setuphelfer-rescue-tui-hold \
  setuphelfer-rescue-physical-e2e-start-gate \
  setuphelfer-rescue-lab-auto-shutdown-failsafe \
  setuphelfer-rescue-msi-rs011b-collect \
  setuphelfer-rescue-physical-e2e; do
  install -m 0755 "${IMAGE}/${script}" "${ROOT}/usr/local/sbin/${script}"
done
install -m 0755 "${IMAGE}/setuphelfer-rescue-auto-e2e-tui-display.py" \
  "${ROOT}/usr/local/sbin/setuphelfer-rescue-auto-e2e-tui-display.py"
for script in setuphelfer-rescue-gui-watchdog.sh setuphelfer-rescue-entrypoint.sh setuphelfer-rescue-tui.sh; do
  install -m 0755 "${IMAGE}/${script}" "${ROOT}/usr/local/sbin/${script%.sh}"
done
install -m 0755 "${REPO_ROOT}/scripts/rescue-live/collect-rescue-runtime-diagnostics.sh" \
  "${ROOT}/usr/local/sbin/collect-rescue-runtime-diagnostics"
for py in setuphelfer-rescue-disk-discovery.py setuphelfer-rescue-plan-builder.py setuphelfer-rescue-live-medium-check.py; do
  install -m 0755 "${IMAGE}/${py}" "${ROOT}/usr/local/sbin/${py}"
done

# RS-P2A: sync workspace backend into live payload (repack previously missed RS-P1 contracts).
RSYNC_EX=(--exclude='__pycache__' --exclude='*.pyc' --exclude='.env' --exclude='tests' --exclude='.pytest_cache' --exclude='venv' --exclude='.venv' --exclude='.venv-ci' --exclude='cache')
mkdir -p "${ROOT}/opt/setuphelfer-rescue/backend" "${ROOT}/opt/setuphelfer-rescue/scripts/rescue-live"
rsync -rlt "${RSYNC_EX[@]}" "${REPO_ROOT}/backend/" "${ROOT}/opt/setuphelfer-rescue/backend/"
rsync -rlt "${RSYNC_EX[@]}" "${REPO_ROOT}/scripts/rescue-live/" "${ROOT}/opt/setuphelfer-rescue/scripts/rescue-live/"

mkdir -p "${ROOT}/opt/setuphelfer-rescue/scripts" "${ROOT}/opt/setuphelfer-rescue/config"
for script in lab-rs-tel-send001-preview.sh lab-rs-tel-send001-send.sh; do
  install -m 0755 "${REPO_ROOT}/scripts/${script}" "${ROOT}/opt/setuphelfer-rescue/scripts/${script}"
done
mkdir -p "${ROOT}/opt/setuphelfer-rescue/scripts/rescue"
install -m 0755 "${REPO_ROOT}/scripts/rescue/collect-msi-rs011b-evidence.sh" \
  "${ROOT}/opt/setuphelfer-rescue/scripts/rescue/collect-msi-rs011b-evidence.sh"
install -m 0755 "${REPO_ROOT}/scripts/create-e2e-backup-test-data.sh" \
  "${ROOT}/opt/setuphelfer-rescue/scripts/create-e2e-backup-test-data.sh"
for cfg in rescue_payload_version.json rescue_telemetry_endpoints.json; do
  [[ -f "${REPO_ROOT}/config/${cfg}" ]] && install -m 0644 "${REPO_ROOT}/config/${cfg}" "${ROOT}/opt/setuphelfer-rescue/config/${cfg}"
done
export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"
python3 - <<PY
import json
from pathlib import Path
from core.rescue_payload_version_carriers import (
    build_rescue_payload_version_json,
    build_rescue_runtime_version_json,
)
root = Path(${ROOT@Q})
cfg_dir = root / "opt/setuphelfer-rescue/config"
cfg_dir.mkdir(parents=True, exist_ok=True)
(cfg_dir / "version.json").write_text(
    json.dumps(build_rescue_runtime_version_json(${PROJECT_VERSION@Q}), indent=2, ensure_ascii=False) + "\\n",
    encoding="utf-8",
)
(cfg_dir / "rescue_payload_version.json").write_text(
    json.dumps(build_rescue_payload_version_json(${PROJECT_VERSION@Q}), indent=2, ensure_ascii=False) + "\\n",
    encoding="utf-8",
)
PY

SYSTEMD="${ROOT}/etc/systemd/system"
WANTS="${SYSTEMD}/multi-user.target.wants"
TIMERS="${SYSTEMD}/timers.target.wants"
mkdir -p "$WANTS" "$TIMERS"
for unit in setuphelfer-rescue-state.service setuphelfer-rescue-evidence-spool.service \
  setuphelfer-rescue-boot-progress.service setuphelfer-rescue-auto-msi-evidence.service \
  setuphelfer-rescue-auto-physical-e2e.service setuphelfer-rescue-auto-discovery.service \
  setuphelfer-rescue-setup-logs-resolver.service \
  setuphelfer-rescue-boot-observer.service \
  setuphelfer-rescue-late-journal-harvest.service \
  setuphelfer-rescue-tui-guard.service \
  setuphelfer-rescue-tui.service; do
  install -m 0644 "${IMAGE}/systemd/${unit}" "${SYSTEMD}/${unit}"
  ln -sf "../${unit}" "${WANTS}/${unit}"
done
install -m 0644 "${IMAGE}/systemd/setuphelfer-rescue-tui-hold.service" \
  "${SYSTEMD}/setuphelfer-rescue-tui-hold.service"
install -m 0644 "${IMAGE}/systemd/setuphelfer-rescue-late-journal-harvest.path" \
  "${SYSTEMD}/setuphelfer-rescue-late-journal-harvest.path"
ln -sf "../setuphelfer-rescue-late-journal-harvest.path" \
  "${WANTS}/setuphelfer-rescue-late-journal-harvest.path"
install -m 0644 "${IMAGE}/systemd/setuphelfer-rescue-tui-guard.timer" \
  "${SYSTEMD}/setuphelfer-rescue-tui-guard.timer"
ln -sf "../setuphelfer-rescue-tui-guard.timer" \
  "${TIMERS}/setuphelfer-rescue-tui-guard.timer"
install -m 0644 "${IMAGE}/systemd/setuphelfer-rescue-boot-observer.timer" \
  "${SYSTEMD}/setuphelfer-rescue-boot-observer.timer"
ln -sf "../setuphelfer-rescue-boot-observer.timer" \
  "${TIMERS}/setuphelfer-rescue-boot-observer.timer"
mkdir -p "${ROOT}/etc/systemd/system.conf.d"
install -m 0644 "${IMAGE}/systemd/system.conf.d/10-setuphelfer-quiet-console.conf" \
  "${ROOT}/etc/systemd/system.conf.d/10-setuphelfer-quiet-console.conf"
# Failsafe: absolute-max timer (3600s) + inactivity watchdog (300s+60s interval).
install -m 0644 "${IMAGE}/systemd/setuphelfer-rescue-lab-auto-shutdown-failsafe.service" \
  "${SYSTEMD}/setuphelfer-rescue-lab-auto-shutdown-failsafe.service"
install -m 0644 "${IMAGE}/systemd/setuphelfer-rescue-lab-auto-shutdown-failsafe.timer" \
  "${SYSTEMD}/setuphelfer-rescue-lab-auto-shutdown-failsafe.timer"
ln -sf "../setuphelfer-rescue-lab-auto-shutdown-failsafe.timer" \
  "${TIMERS}/setuphelfer-rescue-lab-auto-shutdown-failsafe.timer"
install -m 0644 "${IMAGE}/systemd/setuphelfer-rescue-lab-auto-shutdown-watchdog.service" \
  "${SYSTEMD}/setuphelfer-rescue-lab-auto-shutdown-watchdog.service"
install -m 0644 "${IMAGE}/systemd/setuphelfer-rescue-lab-auto-shutdown-watchdog.timer" \
  "${SYSTEMD}/setuphelfer-rescue-lab-auto-shutdown-watchdog.timer"
ln -sf "../setuphelfer-rescue-lab-auto-shutdown-watchdog.timer" \
  "${TIMERS}/setuphelfer-rescue-lab-auto-shutdown-watchdog.timer"
rm -f "${WANTS}/setuphelfer-rescue-lab-auto-shutdown-failsafe.service"
# Late-journal oneshot is path-triggered (MSI marker); avoid eager boot start without marker.
rm -f "${WANTS}/setuphelfer-rescue-late-journal-harvest.service"
# TUI-guard oneshot is timer-triggered; hold screen is on-demand only.
rm -f "${WANTS}/setuphelfer-rescue-tui-guard.service"
rm -f "${WANTS}/setuphelfer-rescue-tui-hold.service"
install -m 0644 "${IMAGE}/systemd/setuphelfer-rescue-ui.service" "${SYSTEMD}/setuphelfer-rescue-ui.service"
# GUI autostart is opt-in via GRUB/TUI; entrypoint orchestrates text default + gui watchdog.
rm -f "${WANTS}/setuphelfer-rescue-ui.service"

# 001D7F: overwrite baked start-assistant so lab/auto cmdline never fights TUI on tty1.
install -m 0644 "${IMAGE}/systemd/setuphelfer-rescue-start-assistant.service" \
  "${SYSTEMD}/setuphelfer-rescue-start-assistant.service"

# Offline-first: network/telemetry not auto-started at boot.
rm -f "${WANTS}/setuphelfer-rescue-network-onboarding.service" \
  "${WANTS}/setuphelfer-rescue-telemetry-push.service" \
  "${TIMERS}/setuphelfer-rescue-telemetry-retry.timer"

install -m 0644 /dev/stdin "${SYSTEMD}/setuphelfer-rescue-network-onboarding.service" <<'EOF'
[Unit]
Description=Setuphelfer Rescue Network Onboarding (user-triggered)
After=NetworkManager.service
Wants=NetworkManager.service
ConditionPathExists=/usr/local/sbin/setuphelfer-rescue-network-onboarding
ConditionPathExists=/run/setuphelfer-rescue/network-user-requested

[Service]
Type=oneshot
RemainAfterExit=yes
TimeoutStartSec=300
ExecStart=/usr/local/sbin/setuphelfer-rescue-network-onboarding --interactive
SuccessExitStatus=0
StandardOutput=journal
StandardError=journal
EOF

install -m 0644 /dev/stdin "${SYSTEMD}/setuphelfer-rescue-telemetry-push.service" <<'EOF'
[Unit]
Description=Setuphelfer Rescue Telemetry Push (opt-in only)
After=setuphelfer-rescue-media-check.service
ConditionPathExists=/usr/local/sbin/setuphelfer-rescue-telemetry-push
ConditionPathExists=/run/setuphelfer-rescue/telemetry-opt-in

[Service]
Type=oneshot
Environment=SETUPHELFER_RESCUE_SCRIPT_DIR=/usr/local/sbin
ExecStart=/usr/local/sbin/setuphelfer-rescue-telemetry-push
SuccessExitStatus=0
StandardOutput=journal
StandardError=journal
EOF

mkdir -p "${ROOT}/etc/systemd/system/systemd-networkd-wait-online.service.d"
install -m 0644 /dev/stdin "${ROOT}/etc/systemd/system/systemd-networkd-wait-online.service.d/10-setuphelfer-rescue.conf" <<'EOF'
[Service]
ExecStart=
ExecStart=/bin/true
TimeoutStartSec=1
EOF

mkdir -p "${ROOT}/usr/share/setuphelfer/rescue"
printf '%s\n' "setuphelfer rescue offline-first boot policy active" > "${ROOT}/usr/share/setuphelfer/rescue/offline-first-boot.marker"
printf '%s\n' "$PROJECT_VERSION" > "${ROOT}/opt/setuphelfer-rescue/VERSION"

RESCUE_BACKEND="${ROOT}/opt/setuphelfer-rescue/backend/rescue"
mkdir -p "$RESCUE_BACKEND"
for mod in rescue_boot_status.py rescue_state.py rescue_evidence_spool.py rescue_machine_profile.py rescue_offline_first_policy.py; do
  install -m 0644 "${REPO_ROOT}/backend/rescue/${mod}" "${RESCUE_BACKEND}/${mod}"
done
echo '"""Setuphelfer rescue runtime modules (live image)."""' > "${RESCUE_BACKEND}/__init__.py"

mkdir -p "${ROOT}/opt/setuphelfer-rescue/i18n"
for loc in de en; do
  [[ -f "${REPO_ROOT}/frontend/src/rescue/i18n/${loc}.json" ]] \
    && install -m 0644 "${REPO_ROOT}/frontend/src/rescue/i18n/${loc}.json" "${ROOT}/opt/setuphelfer-rescue/i18n/${loc}.json"
done

if [[ -d "${REPO_ROOT}/assets/rescue" ]]; then
  mkdir -p "${ROOT}/opt/setuphelfer-rescue/assets"
  cp -a "${REPO_ROOT}/assets/rescue/." "${ROOT}/opt/setuphelfer-rescue/assets/"
  mkdir -p "${ROOT}/usr/share/setuphelfer/rescue/assets"
  cp -a "${REPO_ROOT}/assets/rescue/." "${ROOT}/usr/share/setuphelfer/rescue/assets/"
fi

mksquashfs "$ROOT" "$OUT_SQ" -comp xz -noappend -no-xattrs >/dev/null
NEW_SHA="$(sha256sum "$OUT_SQ" | awk '{print $1}')"
OLD_SHA="$(sha256sum "$SOURCE_SQ" | awk '{print $1}')"

export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"
VERIFY_JSON="$(python3 - <<PY
import json
from pathlib import Path
from core.rescue_squashfs_react_shell_verify import squashfs_verify_launcher_payload
print(json.dumps(squashfs_verify_launcher_payload(Path(${OUT_SQ@Q}))))
PY
)"

python3 - <<PY
import json
from datetime import datetime, timezone
from pathlib import Path

verify = json.loads(${VERIFY_JSON@Q})
launcher_ok = (
    verify.get("contains_react_rescue_shell")
    and verify.get("contains_rescue_ui_launcher_fix")
    and verify.get("contains_fallback_tui")
    and verify.get("contains_network_boot_skip")
    and verify.get("contains_telemetry_default_skipped")
    and verify.get("contains_wait_online_neutralization")
    and (verify.get("checks") or {}).get("chromium_browser")
)
summary = {
    "controlled_iso_build_summary_schema_version": 1,
    "generated_at": datetime.now(tz=timezone.utc).isoformat(),
    "build_status": "success" if launcher_ok else "failed",
    "controlled_lb_build": "not_run",
    "repack_status": "success" if launcher_ok else "failed",
    "build_mode": "squashfs_repack",
    "version": ${PROJECT_VERSION@Q},
    "iso_found": False,
    "iso_path": None,
    "iso_sha256": None,
    "squashfs_path": ${OUT_SQ@Q},
    "squashfs_sha256": ${NEW_SHA@Q},
    "source_squashfs_sha256": ${OLD_SHA@Q},
    "contains_react_rescue_shell": verify.get("contains_react_rescue_shell"),
    "contains_rescue_ui_launcher_fix": verify.get("contains_rescue_ui_launcher_fix"),
    "contains_fallback_tui": verify.get("contains_fallback_tui"),
    "contains_network_boot_skip": verify.get("contains_network_boot_skip"),
    "contains_telemetry_default_skipped": verify.get("contains_telemetry_default_skipped"),
    "contains_wait_online_neutralization": verify.get("contains_wait_online_neutralization"),
    "contains_rescue_ui_manifest": verify.get("contains_rescue_ui_manifest"),
    "contains_offline_first_policy": verify.get("contains_offline_first_policy"),
    "contains_evidence_spool": verify.get("contains_evidence_spool"),
    "contains_machine_profile": verify.get("contains_machine_profile"),
    "network_required_before_menu": verify.get("network_required_before_menu"),
    "telemetry_required_before_menu": verify.get("telemetry_required_before_menu"),
    "no_fake_green": True,
    "squashfs_verify": verify,
}
out = Path(${SUMMARY@Q})
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(summary, indent=2) + "\\n", encoding="utf-8")
print(json.dumps({"squashfs_path": summary["squashfs_path"], "squashfs_sha256": summary["squashfs_sha256"], "contains_react_rescue_shell": summary["contains_react_rescue_shell"]}))
PY

echo "OK: repacked squashfs -> ${OUT_SQ}"
echo "NEW_SQUASHFS_SHA256=${NEW_SHA}"
