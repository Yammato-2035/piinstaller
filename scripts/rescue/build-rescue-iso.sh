#!/usr/bin/env bash
# Setuphelfer rescue ISO build — TEMPLATE ONLY (no live-build, no USB, no host changes unless confirmed).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

if [[ "$(pwd)" != "$ROOT" ]]; then
  echo "build-rescue-iso: working directory mismatch" >&2
  exit 1
fi

OUT_ROOT="${ROOT}/build/rescue"

if [[ "${SETUPHELFER_RESCUE_ISO_BUILD_CONFIRMED:-}" != "1" ]]; then
  echo "build-rescue-iso: dry-run template only. No ISO build, no writes under ${OUT_ROOT}/."
  echo "build-rescue-iso: set SETUPHELFER_RESCUE_ISO_BUILD_CONFIRMED=1 to allow minimal prep (still no dd, mkfs, USB, or systemctl)."
  exit 0
fi

mkdir -p "${OUT_ROOT}/logs"

if ! command -v lb >/dev/null 2>&1; then
  echo "build-rescue-iso: 'lb' (live-build) not found. Install debian live-build on the host manually; no automatic installation is performed." >&2
  exit 2
fi

echo "build-rescue-iso: live-build present; automated lb config/build is not enabled in this template."
exit 0
