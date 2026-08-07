#!/bin/bash
# PI-RS-ASUS-ROOTCAUSE-TELEMETRY-006 — forensic startx wrapper (exitcode + logs always).
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=setuphelfer-rescue-common.sh
source "${SCRIPT_DIR}/setuphelfer-rescue-common.sh" 2>/dev/null || true

RUN_DIR="${SETUPHELFER_STARTX_FORENSIC_DIR:-/run/setuphelfer/startx-forensic}"
VT="${SETUPHELFER_RESCUE_KIOSK_VT:-7}"
STAMP="$(date -u +%Y%m%d_%H%M%S)"
mkdir -p "$RUN_DIR" /var/log 2>/dev/null || true

META="$RUN_DIR/${STAMP}_meta.json"
STDOUT_LOG="$RUN_DIR/${STAMP}_startx.stdout.log"
STDERR_LOG="$RUN_DIR/${STAMP}_startx.stderr.log"
XORG_LOG="${SETUPHELFER_XORG_LOG:-/run/setuphelfer/Xorg.forensic.log}"
SENTINEL="$RUN_DIR/${STAMP}_sentinel.json"
CLASSIFY="$RUN_DIR/${STAMP}_classify.json"

export STARTX_STDOUT_LOG="$STDOUT_LOG"
export STARTX_STDERR_LOG="$STDERR_LOG"

: >"$STDOUT_LOG"
: >"$STDERR_LOG"
: >"$XORG_LOG"

_active_vt="$(fgconsole 2>/dev/null || cat /sys/class/tty/tty0/active 2>/dev/null || echo unknown)"
_tty="$(tty 2>/dev/null || echo none)"
_startx_bin="$(command -v startx 2>/dev/null || true)"
_xinit_bin="$(command -v xinit 2>/dev/null || true)"
_xorg_bin="$(command -v Xorg 2>/dev/null || true)"

python3 - <<PY 2>/dev/null || true
import json, os, pwd, grp, pathlib
meta = {
  "schema_version": 1,
  "timestamp_start": "${STAMP}",
  "uid": os.getuid(),
  "gid": os.getgid(),
  "user": pwd.getpwuid(os.getuid()).pw_name,
  "groups": [grp.getgrgid(g).gr_name for g in os.getgroups()],
  "tty": ${_tty@Q},
  "active_vt": ${_active_vt@Q},
  "target_vt": ${VT@Q},
  "DISPLAY_before": os.environ.get("DISPLAY", ""),
  "XAUTHORITY_before": os.environ.get("XAUTHORITY", ""),
  "HOME": os.environ.get("HOME", ""),
  "PATH": os.environ.get("PATH", ""),
  "startx_binary": ${_startx_bin@Q},
  "xinit_binary": ${_xinit_bin@Q},
  "Xorg_binary": ${_xorg_bin@Q},
  "xinitrc_home": str(pathlib.Path.home() / ".xinitrc"),
  "xinitrc_home_exists": (pathlib.Path.home() / ".xinitrc").is_file(),
  "xserverrc_home_exists": (pathlib.Path.home() / ".xserverrc").is_file(),
  "xorg_log_target": ${XORG_LOG@Q},
  "secrets_exposed": False,
}
pathlib.Path(${META@Q}).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
PY

if [[ -z "$_startx_bin" ]]; then
  printf '{"startx_invoked":false,"startx_exit_code":127,"xorg_started":false,"x_socket_created":false,"xorg_log_created":false}\n' >"$SENTINEL"
  echo "startx_binary_missing" >>"$STDERR_LOG"
  STARTX_EXIT_CODE=127
else
  STARTX_EXIT_CODE=0
  # Hold client: sleep keeps X alive briefly for socket probe; forensic focuses on server start.
  HOLD_CMD="${SETUPHELFER_STARTX_HOLD_CMD:-/bin/true}"
  if [[ -x "${SCRIPT_DIR}/setuphelfer-rescue-x11-hold" ]]; then
    HOLD_CMD="${SCRIPT_DIR}/setuphelfer-rescue-x11-hold"
  fi
  set +e
  "$_startx_bin" "$HOLD_CMD" -- ":0" "vt${VT}" -logfile "$XORG_LOG" \
    >>"$STDOUT_LOG" 2>>"$STDERR_LOG"
  STARTX_EXIT_CODE=$?
  set -e
fi

export STARTX_EXIT_CODE
_xorg_pid="$(pgrep -x Xorg | head -1 || true)"
_xinit_pid="$(pgrep -x xinit | head -1 || true)"
_sock=false
[[ -d /tmp/.X11-unix ]] && ls /tmp/.X11-unix/X* >/dev/null 2>&1 && _sock=true
_log_ok=false
[[ -s "$XORG_LOG" ]] && _log_ok=true
[[ -s /var/log/Xorg.0.log ]] && _log_ok=true

PYTHONPATH="${SETUPHELFER_RESCUE_ROOT:-/opt/setuphelfer-rescue}/backend${PYTHONPATH:+:$PYTHONPATH}" \
python3 - <<PY
import json
from pathlib import Path
try:
    from core.rescue_startx_forensics import build_xorg_process_sentinel, classify_startx_failure
except Exception:
    def build_xorg_process_sentinel(**kw):
        return kw
    def classify_startx_failure(**kw):
        return {"issue_code": "gui.xorg.exited_early", **kw}

sent = build_xorg_process_sentinel(
    startx_invoked=bool(${_startx_bin@Q}),
    startx_pid=0,
    startx_exit_code=int(${STARTX_EXIT_CODE@Q}),
    xinit_started=bool(${_xinit_pid@Q}),
    xorg_started=bool(${_xorg_pid@Q}),
    xorg_pid=int(${_xorg_pid@Q}) if str(${_xorg_pid@Q}).isdigit() else None,
    x_socket_created=${_sock},
    xorg_log_created=${_log_ok},
)
Path(${SENTINEL@Q}).write_text(json.dumps(sent, indent=2) + "\n", encoding="utf-8")
stderr = Path(${STDERR_LOG@Q}).read_text(encoding="utf-8", errors="replace")[-4000:]
cls = classify_startx_failure(
    startx_invoked=bool(${_startx_bin@Q}),
    startx_exit_code=int(${STARTX_EXIT_CODE@Q}),
    xorg_started=bool(${_xorg_pid@Q}),
    xorg_log_created=${_log_ok},
    x_socket_created=${_sock},
    stderr_excerpt=stderr,
)
Path(${CLASSIFY@Q}).write_text(json.dumps(cls, indent=2) + "\n", encoding="utf-8")
print(cls.get("issue_code", "unknown"))
PY

# Best-effort mirror to stick evidence
if command -v setuphelfer_rescue_mirror_evidence_file >/dev/null 2>&1; then
  setuphelfer_rescue_mirror_evidence_file "$META" "setuphelfer/evidence/boot/startx_forensic_meta.json" 2>/dev/null || true
  setuphelfer_rescue_mirror_evidence_file "$STDOUT_LOG" "setuphelfer/logs/boot/startx_forensic.stdout.log" 2>/dev/null || true
  setuphelfer_rescue_mirror_evidence_file "$STDERR_LOG" "setuphelfer/logs/boot/startx_forensic.stderr.log" 2>/dev/null || true
  setuphelfer_rescue_mirror_evidence_file "$SENTINEL" "setuphelfer/evidence/boot/xorg_process_sentinel.json" 2>/dev/null || true
  setuphelfer_rescue_mirror_evidence_file "$CLASSIFY" "setuphelfer/evidence/boot/startx_failure_classify.json" 2>/dev/null || true
  [[ -f "$XORG_LOG" ]] && setuphelfer_rescue_mirror_evidence_file "$XORG_LOG" "setuphelfer/logs/boot/Xorg.forensic.log" 2>/dev/null || true
fi

echo "STARTX_EXIT_CODE=${STARTX_EXIT_CODE}"
exit "${STARTX_EXIT_CODE}"
