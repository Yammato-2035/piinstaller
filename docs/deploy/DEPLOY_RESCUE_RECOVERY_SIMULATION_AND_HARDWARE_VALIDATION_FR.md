> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/deploy/DEPLOY_RESCUE_RECOVERY_SIMULATION_AND_HARDWARE_VALIDATION_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement — Secours recovery simulation & hardware validation (EN)

## Purpose

lecture seule chain for **recovery simulation** on test hardware: scenario matrix, target validation (Non writes), Retourup discovery/verify (SHA256, manifest), **Restauration preview only**, hardware test chain, final readiness gate, operator guides, and evidence timeline (SHA256 over raw bytes).

## API (POST)

Under `/api/Déploiement/Secours/`: `recovery-scenario-matrix`, `recovery-target-validation`, `Retourup-discovery-verify`, `Restauration-preview`, `hardware-recovery-test-chain`, `final-recovery-readiness-gate`, `manual-recovery-operator-guides`, `recovery-evidence-timeline`.

Codes: `Déploiement_Secours_<AREA>_{OK|REVIEW_REQUIrouge|bloqué}`.

## Still forbidden

Non Restauration execute, Non automatic repair, Non `efi-write`, Non Partition/USB write routes — see route tests for forbidden URL segments.

## Versioning

After Succèsful hardware/simulation acceptance: **1.8.0**; **2.0.0** only with real Restauration writes and broader platform coverage.
