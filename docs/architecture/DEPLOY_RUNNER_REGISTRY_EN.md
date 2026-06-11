# Deploy Runner Registry (Phase C.1)

**Status:** Phase C.1 complete  
**Module:** `backend/deploy/runner_registry.py`  
**Registry version:** `REGISTRY_VERSION = 1`

## Why a runner registry?

`backend/deploy/` contains **115** `runner_*.py` files (~37k lines). They are the largest maintenance and scaling risk in deployment: many direct imports in `routes.py`, inconsistent metadata, hard-to-assess risks (USB, ISO, sudo, evidence).

Phase C.1 inventories and types runners **without** refactoring or executing them. The goal is transparency and stable contracts as a basis for later orchestration.

## What is registered?

Each runner gets a static `RunnerRegistryEntry`:

| Field | Meaning |
|-------|---------|
| `runner_id` | Stable ID from filename stem |
| `path` | Relative path to `runner_*.py` |
| `category` | Domain cluster (runtime, rescue_build, …) |
| `risk_level` | Conservative risk class |
| `execution_policy` | Allowed execution modes |
| Capability flags | `writes_files`, `touches_system_paths`, `uses_sudo`, `uses_device_write`, … |
| `has_tests` | Heuristic: matching test file exists |
| `notes` | e.g. `subprocess`, `mount` |

APIs: `build_runner_registry_from_files()`, `classify_runner_file()`, `build_runner_registry_summary()`, `find_runner_by_id()`, `list_runners_by_category()`, `list_runners_by_risk()`, `registry_policy_warnings()`.

Evidence export: `scripts/generate-deploy-runner-registry.py` → `docs/evidence/deploy-runner/runner_registry.generated.json`.

## What is not refactored yet?

- No moving runner files
- No restructuring runner functions
- No lazy import in `routes.py`
- No `app.py` refactoring
- No API facade (→ C.3)
- No result contract (→ C.2)
- No runtime risk gate (→ C.4)

## Why no runner execution in C.1?

Registry and classifier only read file contents (text scan + path heuristics). Runners are **not** imported or invoked — no deploy, backup, restore, ISO build, USB write, or hardware tests.

## Risk levels (`RunnerRiskLevel`)

| Level | Meaning |
|-------|---------|
| `read_only` | Analysis/plan without writes |
| `template_write` | Templates/manifests |
| `evidence_write` | Evidence/docs under workspace |
| `local_runtime_change` | Workspace/lab paths |
| `system_change` | mount, apt, /opt, /etc |
| `device_write` | dd, mkfs, wipefs, sgdisk |
| `destructive` | Device write + high damage potential |

When uncertain, the classifier picks the **higher** risk.

## Execution policies (`RunnerExecutionPolicy`)

| Policy | Meaning |
|--------|-----------|
| `never_auto` | Destructive — never automatic |
| `manual_only` | Manual only |
| `operator_confirmed` | Operator confirmation |
| `lab_only` | Lab/development only |
| `disabled` | Disabled |

Destructive runners get `never_auto`. Sudo without operator policy and device_write without manual policy produce **warnings** in `check-module-boundaries.sh` (warn-only).

## Boundary guard (warn-only)

`scripts/check-module-boundaries.sh` checks:

- `runner_registry_missing` — new `runner_*.py` without registry entry
- `runner_device_write_without_manual_policy`
- `runner_sudo_without_operator_policy`
- `runner_destructive_without_never_auto`

Exit **0** with `status: review_required` — no CI block yet.

## Next phases

| Phase | Content |
|-------|---------|
| **C.2** | Runner result contract — unified result schema |
| **C.3** | Runner API facade — central entry instead of 115 imports |
| **C.4** | Runner risk gate — enforce runtime policy |

## Tests

`backend/tests/test_deploy_runner_registry_v1.py` — import without runtime, heuristics, summary, no runner execution.

## References

- Inventory: `docs/evidence/deploy-runner/DEPLOY_RUNNER_INVENTORY.md`
- DE: `docs/architecture/DEPLOY_RUNNER_REGISTRY.md`
- KB: `docs/knowledge-base/architecture/DEPLOY_RUNNER_REGISTRY_EN.md`
