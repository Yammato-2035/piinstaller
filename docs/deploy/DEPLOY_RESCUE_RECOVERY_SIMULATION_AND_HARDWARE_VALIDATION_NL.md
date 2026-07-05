> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/deploy/DEPLOY_RESCUE_RECOVERY_SIMULATION_AND_HARDWARE_VALIDATION_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy — roodding recovery simulation & hardware validation (EN)

## Purpose

alleen-lezen chain for **recovery simulation** on test hardware: scenario matrix, target validation (Nee writes), Terugup discovery/verify (SHA256, manifest), **Herstel preview only**, hardware test chain, final readiness gate, operator guides, and evidence timeline (SHA256 over raw bytes).

## API (POST)

Under `/api/Deploy/roodding/`: `recovery-scenario-matrix`, `recovery-target-validation`, `Terugup-discovery-verify`, `Herstel-preview`, `hardware-recovery-test-chain`, `final-recovery-readiness-gate`, `manual-recovery-operator-guides`, `recovery-evidence-timeline`.

Codes: `Deploy_roodding_<AREA>_{OK|REVIEW_REQUIrood|geblokkeerd}`.

## Still forbidden

Nee Herstel execute, Nee automatic repair, Nee `efi-write`, Nee Partitie/USB write routes — see route tests for forbidden URL segments.

## Versioning

After Geslaagdful hardware/simulation acceptance: **1.8.0**; **2.0.0** only with real Herstel writes and broader platform coverage.
