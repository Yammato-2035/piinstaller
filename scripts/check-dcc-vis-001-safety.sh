#!/usr/bin/env bash
# DCC-VIS-001 safety gate — no secrets, no fake greens, no deploy triggers in visibility layer.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
FAIL=0

die() { echo "DCC-VIS-001 SAFETY FAIL: $*" >&2; FAIL=1; }

# No hardcoded developer tokens or fake secrets in visibility code
if rg -n 'fake-local-hmac-secret' \
  frontend/src/dcc frontend/src/components/dev-dashboard/DccRuntimeStatusPanel.tsx \
  frontend/src/components/dev-dashboard/DccDeveloperTokenCard.tsx \
  frontend/src/components/dev-dashboard/DccVisibleResultsPanel.tsx \
  frontend/src/lib/devDashboard/dccDeveloperToken.ts 2>/dev/null; then
  die "hardcoded secret in DCC visibility layer"
fi

# Evidence must not contain token values
if rg -l 'setuphelfer-dcc-developer-token|gho_[A-Za-z0-9]+' docs/evidence/DCC_VIS_001*.md 2>/dev/null; then
  die "token leak in DCC_VIS_001 evidence"
fi

# No production URLs in new visibility stubs
if rg -n 'https://beta\.setuphelfer\.de|https://telemetry\.setuphelfer' \
  frontend/src/dcc/visibility docs/faq/DCC_VIS_001* docs/kb/DCC_VIS_001* 2>/dev/null; then
  die "production URL in DCC-VIS-001 stubs"
fi

# No backup/restore/deploy execution in visibility components
if rg -n 'deploy-to-opt|restore-from-backup|mkfs' \
  frontend/src/dcc/visibility \
  frontend/src/components/dev-dashboard/DccVisibleResultsPanel.tsx \
  frontend/src/components/dev-dashboard/DccVisibilityRoadmapSection.tsx 2>/dev/null; then
  die "dangerous deploy/backup pattern in visibility UI"
fi

# FAQ/KB stubs must exist
for f in \
  docs/faq/DCC_VIS_001_FAQ.de.md \
  docs/faq/DCC_VIS_001_FAQ.en.md \
  docs/kb/DCC_VIS_001_KB.de.md \
  docs/kb/DCC_VIS_001_KB.en.md; do
  [[ -f "$f" ]] || die "missing doc stub: $f"
done

# i18n keys present for de/en/fr/nl
for loc in dccVis001.de.json dccVis001.en.json dccVis001.fr.json dccVis001.nl.json; do
  [[ -f "frontend/src/locales/$loc" ]] || die "missing locale: $loc"
done

if [[ "$FAIL" -ne 0 ]]; then
  exit 1
fi
echo "check-dcc-vis-001-safety: ok"
