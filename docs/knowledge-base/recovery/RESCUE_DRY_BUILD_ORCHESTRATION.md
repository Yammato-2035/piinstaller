# Rescue — Dry Build Orchestration (KB)

## Zweck

Die Dry-Build-Orchestrierung fasst **Planungs- und Validierungsstufen** zusammen, die spaeter einen echten Debian-Live-Rescue-Build begleiten koennten. Sie erzeugt **nur** JSON unter `build/rescue/` und Evidence-Handoffs — keine Image-Erzeugung, kein `lb build`, kein Chroot.

## Ablauf (logisch)

1. Runtime-Bundle-Checks (Konsistenz, Seal-Pfade)  
2. Debian-Live-Build-Inputs (Konfiguration, Listen, Templates)  
3. Runtime-Assembly- und Pseudo-Boot-Gates  
4. Safety-Scan und finales Dry-Gate  

## Verweise

- Deploy (DE): `docs/deploy/DEPLOY_RESCUE_DRY_BUILD_ORCHESTRATION_DE.md`
- Deploy (EN): `docs/deploy/DEPLOY_RESCUE_DRY_BUILD_ORCHESTRATION_EN.md`
- Evidence: `docs/evidence/DEPLOY_RESCUE_DRY_BUILD_ORCHESTRATION.md`
- Runner: `backend/deploy/runner_rescue_dry_build_orchestration.py`
