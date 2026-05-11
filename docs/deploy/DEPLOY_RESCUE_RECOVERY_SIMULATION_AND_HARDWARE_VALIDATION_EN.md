# Deploy — Rescue recovery simulation & hardware validation (EN)

## Purpose

Read-only chain for **recovery simulation** on test hardware: scenario matrix, target validation (no writes), backup discovery/verify (SHA256, manifest), **restore preview only**, hardware test chain, final readiness gate, operator guides, and evidence timeline (SHA256 over raw bytes).

## API (POST)

Under `/api/deploy/rescue/`: `recovery-scenario-matrix`, `recovery-target-validation`, `backup-discovery-verify`, `restore-preview`, `hardware-recovery-test-chain`, `final-recovery-readiness-gate`, `manual-recovery-operator-guides`, `recovery-evidence-timeline`.

Codes: `DEPLOY_RESCUE_<AREA>_{OK|REVIEW_REQUIRED|BLOCKED}`.

## Still forbidden

No restore execute, no automatic repair, no `efi-write`, no partition/USB write routes — see route tests for forbidden URL segments.

## Versioning

After successful hardware/simulation acceptance: **1.8.0**; **2.0.0** only with real restore writes and broader platform coverage.
