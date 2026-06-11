# Deploy Runner Registry — Kurzreferenz (KB)

**Phase:** C.1 (Inventar + statische Registry)  
**Modul:** `backend/deploy/runner_registry.py`

## Kernpunkte

- **115** Deploy-Runner unter `backend/deploy/runner_*.py` — noch **nicht** refaktoriert
- Registry beschreibt Runner nur **statisch** (kein Import, keine Ausführung)
- Classifier: Dateiname + Textscan → Kategorie, Risiko, Execution Policy
- Export: `python3 scripts/generate-deploy-runner-registry.py`
- Boundary: warn-only Policy-Warnungen in `check-module-boundaries.sh`

## Kategorien

`runtime`, `deploy`, `rescue`, `rescue_build`, `rescue_usb`, `backup_related`, `restore_related`, `notification`, `evidence`, `packaging`, `dashboard`, `diagnostics`, `unknown`

## Risiko / Policy

Siehe `docs/architecture/DEPLOY_RUNNER_REGISTRY.md` — bei Unsicherheit höheres Risiko.

## Nächster Schritt

**C.2** Runner Result Contract

## Dateien

| Artefakt | Pfad |
|----------|------|
| Registry-Code | `backend/deploy/runner_registry.py` |
| Tests | `backend/tests/test_deploy_runner_registry_v1.py` |
| Generator | `scripts/generate-deploy-runner-registry.py` |
| Inventar | `docs/evidence/deploy-runner/` |
