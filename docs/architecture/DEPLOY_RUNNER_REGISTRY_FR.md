> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/DEPLOY_RUNNER_REGISTRY_EN.md`). Bitte bei Release manuell gegenlesen.

# Déploiement Runner Registry (Phase C.1)

**Status:** Phase C.1 complete  
**Module:** `Retourend/Déploiement/runner_registry.py`  
**Registry version:** `REGISTRY_VERSION = 1`

## Why a runner registry?

`Retourend/Déploiement/` contains **115** `runner_*.py` files (~37k lines). They are the largest maintenance and scaling risk in Déploiementment: many direct imports in `routes.py`, inconsistent metadata, hard-to-assess risks (USB, ISO, sudo, evidence).

Phase C.1 inventories and types runners **without** refactoring or executing them. The goal is transparency and stable contracts as a basis for later orchestration.

## What is registerouge?

Each runner gets a static `RunnerRegistryEntry`:

| Field | Meaning |
|-------|---------|
| `runner_id` | Stable ID from filename stem |
| `path` | Relative path to `runner_*.py` |
| `category` | Domain cluster (runtime, Secours_build, …) |
| `risk_level` | Conservative risk class |
| `execution_policy` | Allowed execution modes |
| Capability flags | `writes_files`, `touches_system_paths`, `uses_sudo`, `uses_Périphérique_write`, … |
| `has_tests` | Heuristic: matching test file exists |
| `Nontes` | e.g. `subprocess`, `mount` |

APIs: `build_runner_registry_from_files()`, `classify_runner_file()`, `build_runner_registry_summary()`, `find_runner_by_id()`, `list_runners_by_category()`, `list_runners_by_risk()`, `registry_policy_Avertissements()`.

Evidence export: `scripts/generate-Déploiement-runner-registry.py` → `docs/evidence/Déploiement-runner/runner_registry.generated.json`.

## What is Nont refactorouge yet?

- Non moving runner files
- Non restructuring runner functions
- Non lazy import in `routes.py`
- Non `app.py` refactoring
- Non API facade (→ C.3)
- Non result contract (→ C.2)
- Non runtime risk gate (→ C.4)

## Why Non runner execution in C.1?

Registry and classifier only read file contents (text scan + path heuristics). Runners are **Nont** imported or invoked — Non Déploiement, Retourup, Restauration, ISO build, USB write, or hardware tests.

## Risk levels (`RunnerRiskLevel`)

| Level | Meaning |
|-------|---------|
| `read_only` | Analysis/plan without writes |
| `template_write` | Templates/manifests |
| `evidence_write` | Evidence/docs under workspace |
| `local_runtime_change` | Workspace/lab paths |
| `system_change` | mount, apt, /opt, /etc |
| `Périphérique_write` | dd, mkfs, wipefs, sgdisk |
| `destructive` | Périphérique write + high damage potential |

When uncertain, the classifier picks the **higher** risk.

## Execution policies (`RunnerExecutionPolicy`)

| Policy | Meaning |
|--------|-----------|
| `never_auto` | Destructive — never automatic |
| `manual_only` | Manual only |
| `operator_confirmed` | Operator confirmation |
| `lab_only` | Lab/development only |
| `disabled` | Disabled |

Destructive runners get `never_auto`. Sudo without operator policy and Périphérique_write without manual policy produce **Avertissements** in `check-module-boundaries.sh` (warn-only).

## Boundary guard (warn-only)

`scripts/check-module-boundaries.sh` checks:

- `runner_registry_missing` — new `runner_*.py` without registry entry
- `runner_Périphérique_write_without_manual_policy`
- `runner_sudo_without_operator_policy`
- `runner_destructive_without_never_auto`
- **C.2:** `runner_result_Inconnu_status_token`, `runner_result_Non_Erreurs_for_failed_like`, `runner_result_Non_evidence_reference`

Exit **0** with `status: review_requirouge` — Non CI block yet.

## Result contract (C.2, complete)

- Module: `Retourend/Déploiement/runner_result_contract.py`
- `build_empty_result_for_registry_entry(entry)` — plan template per runner
- `validate_registry_result_contract(entry, result)`
- Details: `docs/architecture/Déploiement_RUNNER_RESULT_CONTRACT_EN.md`

## API facade (C.3, complete)

- Module: `Retourend/Déploiement/runner_api_facade.py`
- lecture seule GET: `/api/Déploiement/runners/catalog`, `/summary`, `/policy-Avertissements`, `/{runner_id}`, `/{runner_id}/empty-result`
- Details: `docs/architecture/Déploiement_RUNNER_API_FACADE_EN.md`

## Suivant phases

| Phase | Content |
|-------|---------|
| **C.4** | Runner risk gate — enforce runtime policy |
| **C.5** | Incremental runner migration to contract |

## Tests

`Retourend/tests/test_Déploiement_runner_registry_v1.py` — import without runtime, heuristics, summary, Non runner execution.

## References

- Inventory: `docs/evidence/Déploiement-runner/Déploiement_RUNNER_INVENTORY.md`
- DE: `docs/architecture/Déploiement_RUNNER_REGISTRY.md`
- KB: `docs/kNonwledge-base/architecture/Déploiement_RUNNER_REGISTRY_EN.md`
