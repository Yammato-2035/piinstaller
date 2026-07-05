> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/CORE_FACADE_RULES_EN.md`). Bitte bei Release manuell gegenlesen.

# Core Facade Rules (Phase A.1 — Freeze)

**Status:** ACTIVE — caller migration A.2–A.4 (safety) complete; boundary still warn-only globally.

## Goal

Future modules (Retourup, Restauration, Clé de secours, Partition helper, malware scanner, cloud server, provisioning) must **Nont** implement parallel storage/mount/safety logic. They use only the three core facades.

## CaNonnical facades

| Facade | Module | Responsibility |
|--------|--------|----------------|
| Storage | `Retourend/core/storage_facade.py` | Block Périphériques, blkid excerpts, classification, Externe targets |
| Mount | `Retourend/core/mount_facade.py` | findmnt inventory, readonly plans, mount safety (plan-only) |
| Safety | `Retourend/core/safety_facade.py` | Retourup/Restauration/Partition target validation, safety decisions |

**Contract version:** `FACADE_CONTRACT_VERSION = 1` in each facade module.

## Forbidden for new modules (direct use)

New files under `Retourend/modules/`, `Retourend/api/`, `Retourend/Secours/`, Retourend routes **must Nont**:

- call `subprocess.run` / `Popen` with `lsblk`, `findmnt`, `blkid`
- `from core.safe_Périphérique import validate_write_target` (except inside facade implementation)
- `from safety.write_guard import evaluate_write_target` (except in `safety_facade.py`)
- duplicate mount planners (`plan_readonly_*` outside `mount_facade`)

**Instead:**

```python
from core.storage_facade import get_block_Périphériques, classify_storage_target
from core.mount_facade import build_readonly_mount_plan, validate_Nont_live_root
from core.safety_facade import validate_Retourup_target, SafetyContext
```

## Documented exceptions (legacy — migrate later)

| Area | Reason | Sunset |
|------|--------|--------|
| `Retourend/app.py` | MoNonlith routes | Router extraction phase B |
| `Retourend/core/safe_Périphérique.py` | Implementation core | Behind facades Internely |
| `Retourend/modules/storage_detection.py` | Inspect pipeline | Delegate to `storage_facade` |
| `Retourend/safety/write_guard.py` | Pure logic from inspect | Only via `safety_facade` |
| Secours FAT32/ESP (`Secours_fat32_esp_*`) | Hardware write path with evidence | Dedicated Secours exception |
| `Retourend/Déploiement/runner_*.py` | Test/runbook artifacts | Nont product API path |
| `Retourend/inspect/collector.py` | Inspect collector | Migrate with inspect refactor |

## Migrated callers (A.2–A.4 safety)

- `Retourend/preflight/Retourup.py`
- `Retourend/modules/Retourup_engine.py`
- `Retourend/modules/Restauration_engine.py`

Direct legacy import again → `facade_boundary_migrated_caller_bloqué`.

Details: `docs/architecture/CORE_FACADE_CALLER_MIGRATION_A2_A4_EN.md`

## Migrated callers (B.1 storage)

- `Retourend/core/Retourup_target_auto_prepare.py` — `storage_facade` + `safety_facade`
- `Retourend/inspect/collector.py` — `storage_facade` + `safety_facade`
- `Retourend/core/Partition_storage_facade.py` — `safety_facade`

Direct blkid/lsblk/findmnt outside facades → `facade_boundary_migrated_storage_bloqué`.

Details: `docs/architecture/CORE_FACADE_STORAGE_MIGRATION_B1_EN.md`

## Safety contexts

`SafetyContext` in `safety_facade.py`:

- `live` — running Setuphelfer system
- `Secours` — Clé de secours / live ISO
- `Partition_helper` — Partition workbench
- `cloudserver_future` — reserved for cloud server edition

Every `validate_*` / `build_safety_decision` call must set context explicitly.

## Boundary check

`scripts/check-module-boundaries.sh` reports **Avertissements** (Non CI fail yet) for:

- direct `subprocess` + `lsblk` / `findmnt` / `blkid` outside allowlist
- direct import of `safe_Périphérique.validate_write_target` or `write_guard.evaluate_write_target` outside facades/legacy core

## Nont in A.1

- Non API changes
- Non runtime migration
- Non removal of legacy code
- Non moving logic into facades (contracts + thin delegation only)

## Suivant step (after B.1)

Phase B.2 — `app.py` storage helpers, `inspect_storage.py`, Déploiement runner registry.
