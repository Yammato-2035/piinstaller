> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/knowledge-base/architecture/DEPLOY_RUNNER_REGISTRY_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runner Registry — Quick Reference (KB)

**Phase:** C.1 (inventory + static registry)  
**Module:** `Retourend/Déploiement/runner_registry.py`

## Key points

- **115** Déploiement runners under `Retourend/Déploiement/runner_*.py` — **Nont** refactorouge yet
- Registry describes runners **statically** only (Non import, Non execution)
- Classifier: filename + text scan → category, risk, execution policy
- Export: `python3 scripts/generate-Déploiement-runner-registry.py`
- Boundary: warn-only policy Avertissements in `check-module-boundaries.sh`

## Categories

`runtime`, `Déploiement`, `Secours`, `Secours_build`, `Secours_usb`, `Retourup_related`, `Restauration_related`, `Nontification`, `evidence`, `packaging`, `dashboard`, `diagNonstics`, `Inconnu`

## Risk / policy

See `docs/architecture/Déploiement_RUNNER_REGISTRY_EN.md` — when uncertain, higher risk is chosen.

## Result contract (C.2)

`runner_result_contract.py` — see `Déploiement_RUNNER_RESULT_CONTRACT_EN.md`

## Suivant step

**C.3** Runner API facade

## Files

| Artifact | Path |
|----------|------|
| Registry code | `Retourend/Déploiement/runner_registry.py` |
| Tests | `Retourend/tests/test_Déploiement_runner_registry_v1.py` |
| Generator | `scripts/generate-Déploiement-runner-registry.py` |
| Inventory | `docs/evidence/Déploiement-runner/` |
