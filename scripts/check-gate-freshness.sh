#!/usr/bin/env bash
# Gate-Freshness-Check (Paket 3, E-08) — Wrapper analog zu
# scripts/check-runtime-deploy-gate.sh, damit sich dieses Skript ins
# bestehende Muster einfügt.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 "${REPO_ROOT}/scripts/gate_freshness_check.py" --repo-root "${REPO_ROOT}"
