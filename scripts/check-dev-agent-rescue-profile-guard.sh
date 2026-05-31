#!/usr/bin/env bash
# Static guard: Rescue Developer vs Public profile separation for Dev Agent.
# Exit: 0 OK | 10 dev missing | 11 public upload | 12 public URL | 13 secret
#       14 dangerous cmd | 15 ssh | 16 write | 17 remote public | 18 ssh fwd public
#       19 german keyboard | 20 unknown

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEV_PROFILE="${REPO_ROOT}/build/rescue/profiles/developer"
QEMU_PROFILE="${REPO_ROOT}/build/rescue/profiles/developer-qemu"
PUB_PROFILE="${REPO_ROOT}/build/rescue/profiles/public"

err() { echo "[GUARD] $*" >&2; }

if [[ ! -d "$DEV_PROFILE" ]]; then
  err "developer profile missing: $DEV_PROFILE"
  exit 10
fi

export PYTHONPATH="${REPO_ROOT}/backend:${REPO_ROOT}"

RESULT="$(cd "$REPO_ROOT" && python3 -c "
from pathlib import Path
import json
from devserver_agent.rescue_profile import (
    validate_developer_profile,
    validate_developer_qemu_profile,
    validate_public_profile_guard,
)
dev = validate_developer_profile(Path('build/rescue/profiles/developer'))
pub = validate_public_profile_guard(Path('build/rescue/profiles/public'))
qemu = None
qp = Path('build/rescue/profiles/developer-qemu')
if qp.is_dir():
    qemu = validate_developer_qemu_profile(qp)
print(json.dumps({'developer': dev, 'public': pub, 'developer_qemu': qemu}))
")"

DEV_OK="$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['developer']['ok'])" "$RESULT")"
PUB_OK="$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['public']['ok'])" "$RESULT")"

if [[ "$DEV_OK" != "True" ]]; then
  err "developer profile validation failed"
  python3 -c "import json,sys; [print(e) for e in json.loads(sys.argv[1])['developer'].get('errors',[])]" "$RESULT" >&2
  exit 10
fi

if [[ -d "$QEMU_PROFILE" ]]; then
  QEMU_OK="$(python3 -c "import json,sys; q=json.loads(sys.argv[1]).get('developer_qemu'); print(q['ok'] if q else False)" "$RESULT")"
  if [[ "$QEMU_OK" != "True" ]]; then
    err "developer-qemu profile validation failed"
    python3 -c "import json,sys; q=json.loads(sys.argv[1]).get('developer_qemu') or {}; [print(e) for e in q.get('errors',[])]" "$RESULT" >&2
    exit 10
  fi
fi

if [[ "$PUB_OK" != "True" ]]; then
  PUB_ERRORS="$(python3 -c "import json,sys; print(','.join(json.loads(sys.argv[1])['public'].get('errors',[])))" "$RESULT")"
  case "$PUB_ERRORS" in
    *public_auto_upload*) exit 11 ;;
    *server_url*) exit 12 ;;
    *secret_or_token*) exit 13 ;;
    *forbidden_token*) exit 14 ;;
    *ssh*) exit 15 ;;
    *write*) exit 16 ;;
    *remote_console_public_exposure*) exit 17 ;;
    *remote_bind_all_interfaces*) exit 17 ;;
    *ssh_forward*) exit 18 ;;
    *german_keyboard*) exit 19 ;;
    *) err "public guard failed: $PUB_ERRORS"; exit 20 ;;
  esac
fi

scan_file() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  if grep -Ei '(SETUPHELFER_DEV_AGENT_TOKEN|password|secret=|api_key=)' "$f" >/dev/null 2>&1; then
    err "secret/token pattern in $f"
    exit 13
  fi
  if grep -Ei '\bdd\b|\bmkfs\b|\bmount\b|\bumount\b|\bparted\b|\bsfdisk\b|\bsgdisk\b|\bwipefs\b|\bsudo\b|\bapt\b|rm -rf|debootstrap|lb build' "$f" >/dev/null 2>&1; then
    err "dangerous command pattern in $f"
    exit 14
  fi
}

for f in \
  "$DEV_PROFILE/environment/setuphelfer-dev-agent.env" \
  "$DEV_PROFILE/systemd/setuphelfer-dev-agent.service" \
  "$DEV_PROFILE/manifest.json" \
  "$PUB_PROFILE/environment/setuphelfer-dev-agent.env" \
  "$PUB_PROFILE/manifest.json"; do
  scan_file "$f"
done

if [[ -d "$QEMU_PROFILE" ]]; then
  for f in \
    "$QEMU_PROFILE/environment/setuphelfer-dev-agent.env" \
    "$QEMU_PROFILE/systemd/setuphelfer-dev-agent.service" \
    "$QEMU_PROFILE/manifest.json"; do
    scan_file "$f"
  done
  if grep -q '0.0.0.0' "$QEMU_PROFILE/manifest.json" 2>/dev/null; then
    err "developer-qemu manifest must not bind 0.0.0.0"
    exit 17
  fi
fi

if grep -q 'SETUPHELFER_DEV_AGENT_AUTO_UPLOAD=true' "$PUB_PROFILE/environment/setuphelfer-dev-agent.env" 2>/dev/null; then
  err "public profile has AUTO_UPLOAD=true"
  exit 11
fi

if ! grep -q 'NoNewPrivileges=true' "$DEV_PROFILE/systemd/setuphelfer-dev-agent.service" 2>/dev/null; then
  err "developer systemd missing NoNewPrivileges"
  exit 14
fi

echo "[GUARD] OK — developer profile valid, public auto-upload blocked"
exit 0
