# Deploy — Rescue Recovery-Simulation & Hardware-Validierung (DE)

## Zweck

Readonly-Kette für **Recovery-Simulation** auf Testhardware: Szenario-Matrix, Zielvalidierung (ohne Writes), Backup-Discovery/Verify (SHA256, Manifest), **nur** Restore-Preview, Hardware-Testkette, finales Readiness-Gate, Operator-Guides und Evidence-Timeline (SHA256 über Rohbytes).

## API (POST)

Unter `/api/deploy/rescue/`: `recovery-scenario-matrix`, `recovery-target-validation`, `backup-discovery-verify`, `restore-preview`, `hardware-recovery-test-chain`, `final-recovery-readiness-gate`, `manual-recovery-operator-guides`, `recovery-evidence-timeline`.

Antwortcodes: `DEPLOY_RESCUE_<BEREICH>_{OK|REVIEW_REQUIRED|BLOCKED}`.

## Verbote

Kein Restore-Execute, keine automatische Reparatur, kein `efi-write`, keine Partition-USB-Schreibpfade — siehe Routen-Tests auf verbotene URL-Segmente.

## Version

Nach erfolgreicher Hardware-/Simulationsabnahme: **1.8.0**; **2.0.0** erst mit echten Restore-Writes und breiter Plattformabdeckung.
