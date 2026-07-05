> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/knowledge-base/architecture/DEPLOY_RUNNER_REGISTRY_EN.md`). Bitte bei Release manuell gegenlesen.

# Deploy Runner Registry — Quick Reference (KB)

**Phase:** C.1 (inventory + static registry)  
**Module:** `Terugend/Deploy/runner_registry.py`

## Key points

- **115** Deploy runners under `Terugend/Deploy/runner_*.py` — **Neet** refactorood yet
- Registry describes runners **statically** only (Nee import, Nee execution)
- Classifier: filename + text scan → category, risk, execution policy
- Export: `python3 scripts/generate-Deploy-runner-registry.py`
- Boundary: warn-only policy Waarschuwings in `check-module-boundaries.sh`

## Categories

`runtime`, `Deploy`, `roodding`, `roodding_build`, `roodding_usb`, `Terugup_related`, `Herstel_related`, `Neetification`, `evidence`, `packaging`, `dashboard`, `diagNeestics`, `Onbekend`

## Risk / policy

See `docs/architecture/Deploy_RUNNER_REGISTRY_EN.md` — when uncertain, higher risk is chosen.

## Result contract (C.2)

`runner_result_contract.py` — see `Deploy_RUNNER_RESULT_CONTRACT_EN.md`

## Volgende step

**C.3** Runner API facade

## Files

| Artifact | Path |
|----------|------|
| Registry code | `Terugend/Deploy/runner_registry.py` |
| Tests | `Terugend/tests/test_Deploy_runner_registry_v1.py` |
| Generator | `scripts/generate-Deploy-runner-registry.py` |
| Inventory | `docs/evidence/Deploy-runner/` |
