# Deploy Legacy Identifier Hotspot Analysis

Strict-mode **read-only** step: merge active-runtime hits from inventory (and optionally postcheck + consistency handoff), assign **clusters** and **criticality**, emit `legacy_identifier_hotspot_analysis.json` under `docs/evidence/runtime-results/handoff/`.

- **Runner:** `backend/deploy/runner_legacy_identifier_hotspot_analysis.py` (`build_legacy_identifier_hotspot_analysis`)
- **Route:** `POST /api/deploy/legacy-identifier-hotspot-analysis`
- **Contract / DE+EN:** `docs/deploy/DEPLOY_LEGACY_IDENTIFIER_HOTSPOT_ANALYSIS_DE.md`, `docs/deploy/DEPLOY_LEGACY_IDENTIFIER_HOTSPOT_ANALYSIS_EN.md`
- **Evidence index:** `docs/evidence/DEPLOY_LEGACY_IDENTIFIER_HOTSPOT_ANALYSIS.md`

No subprocess/systemctl, no rewrites, no version bump (1.7.0).
