# Evidence — Deploy Rescue Stick Build Preparation

## Zweck

Nachweis- und Handoff-Kette fuer den **Rettungsstick-Build-Strang** (Planung only): Live-OS-Entscheidung, Komponenten-Inventar, MVP-Scope, Debian-Live-Buildplan, ISO-Testmatrix, Build-Readiness.

## Artefakte

| Datei | Beschreibung |
|--------|----------------|
| `docs/evidence/runtime-results/handoff/rescue_live_os_base_decision.json` | Empfohlene Basis (Debian Live), Secure-Boot-Hinweis |
| `docs/evidence/runtime-results/handoff/rescue_stick_component_inventory.json` | existing/partial/missing |
| `docs/evidence/runtime-results/handoff/rescue_mvp_scope_gate.json` | MVP-Includes/Excludes |
| `docs/evidence/runtime-results/handoff/rescue_debian_live_build_plan.json` | Paketgruppen, nur `build/rescue/` |
| `docs/evidence/runtime-results/handoff/rescue_iso_test_matrix.json` | VM + Laptop + later |
| `docs/evidence/runtime-results/handoff/rescue_build_readiness_gate.json` | Aggregiertes Gate |

## Verweise

- Architektur: `docs/rescue/SETUPHELFER_RESCUE_STICK_ARCHITECTURE_DE.md` / `_EN.md`
- Safety: `docs/developer/RESCUE_STICK_BUILD_SAFETY_POLICY.md`
- Deploy: `docs/deploy/DEPLOY_RESCUE_STICK_BUILD_PREPARATION_DE.md` / `_EN.md`
