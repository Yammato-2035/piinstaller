#!/usr/bin/env bash
# Controlled Setuphelfer rescue ISO build — workspace-only, no USB/dd/mkfs/wipefs/host systemctl.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

if [[ "$(pwd)" != "$ROOT" ]]; then
  echo "build-rescue-iso-controlled: working directory mismatch" >&2
  exit 1
fi

WS="${ROOT}/build/rescue"
OUT="${WS}/output"
LOG="${WS}/logs"
LBDIR="${WS}/live-build"

mkdir -p "${OUT}" "${LOG}" "${LBDIR}" "${WS}/evidence"

if [[ "${SETUPHELFER_RESCUE_BUILD_APPROVED:-}" != "1" ]]; then
  echo "build-rescue-iso-controlled: dry-run (no live-build). Set SETUPHELFER_RESCUE_BUILD_APPROVED=1 to attempt a build."
  exit 0
fi

if ! command -v lb >/dev/null 2>&1; then
  echo "build-rescue-iso-controlled: live-build (lb) not found" >&2
  exit 2
fi

if [[ ! -f "${LBDIR}/auto/config" ]]; then
  echo "build-rescue-iso-controlled: no materialized live-build config at ${LBDIR}/auto/config (generate config first)." >&2
  exit 3
fi

(
  cd "${LBDIR}"
  lb build 2>&1 | tee "${LOG}/lb-build.log"
)
