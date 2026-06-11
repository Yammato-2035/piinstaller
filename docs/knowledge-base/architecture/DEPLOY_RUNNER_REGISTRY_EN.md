# Deploy Runner Registry — Quick Reference (KB)

**Phase:** C.1 (inventory + static registry)  
**Module:** `backend/deploy/runner_registry.py`

## Key points

- **115** deploy runners under `backend/deploy/runner_*.py` — **not** refactored yet
- Registry describes runners **statically** only (no import, no execution)
- Classifier: filename + text scan → category, risk, execution policy
- Export: `python3 scripts/generate-deploy-runner-registry.py`
- Boundary: warn-only policy warnings in `check-module-boundaries.sh`

## Categories

`runtime`, `deploy`, `rescue`, `rescue_build`, `rescue_usb`, `backup_related`, `restore_related`, `notification`, `evidence`, `packaging`, `dashboard`, `diagnostics`, `unknown`

## Risk / policy

See `docs/architecture/DEPLOY_RUNNER_REGISTRY_EN.md` — when uncertain, higher risk is chosen.

## Result contract (C.2)

`runner_result_contract.py` — see `DEPLOY_RUNNER_RESULT_CONTRACT_EN.md`

## Next step

**C.3** Runner API facade

## Files

| Artifact | Path |
|----------|------|
| Registry code | `backend/deploy/runner_registry.py` |
| Tests | `backend/tests/test_deploy_runner_registry_v1.py` |
| Generator | `scripts/generate-deploy-runner-registry.py` |
| Inventory | `docs/evidence/deploy-runner/` |
