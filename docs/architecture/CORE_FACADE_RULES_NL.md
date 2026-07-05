> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/CORE_FACADE_RULES_EN.md`). Bitte bei Release manuell gegenlesen.

# Core Facade Rules (Phase A.1 — Freeze)

**Status:** ACTIVE — caller migration A.2–A.4 (safety) complete; boundary still warn-only globally.

## Goal

Future modules (Terugup, Herstel, rooddingsstick, Partitie helper, malware scanner, cloud server, provisioning) must **Neet** implement parallel storage/mount/safety logic. They use only the three core facades.

## CaNeenical facades

| Facade | Module | Responsibility |
|--------|--------|----------------|
| Storage | `Terugend/core/storage_facade.py` | Block Apparaats, blkid excerpts, classification, Extern targets |
| Mount | `Terugend/core/mount_facade.py` | findmnt inventory, readonly plans, mount safety (plan-only) |
| Safety | `Terugend/core/safety_facade.py` | Terugup/Herstel/Partitie target validation, safety decisions |

**Contract version:** `FACADE_CONTRACT_VERSION = 1` in each facade module.

## Forbidden for new modules (direct use)

New files under `Terugend/modules/`, `Terugend/api/`, `Terugend/roodding/`, Terugend routes **must Neet**:

- call `subprocess.run` / `Popen` with `lsblk`, `findmnt`, `blkid`
- `from core.safe_Apparaat import validate_write_target` (except inside facade implementation)
- `from safety.write_guard import evaluate_write_target` (except in `safety_facade.py`)
- duplicate mount planners (`plan_readonly_*` outside `mount_facade`)

**Instead:**

```python
from core.storage_facade import get_block_Apparaats, classify_storage_target
from core.mount_facade import build_readonly_mount_plan, validate_Neet_live_root
from core.safety_facade import validate_Terugup_target, SafetyContext
```

## Documented exceptions (legacy — migrate later)

| Area | Reason | Sunset |
|------|--------|--------|
| `Terugend/app.py` | MoNeelith routes | Router extraction phase B |
| `Terugend/core/safe_Apparaat.py` | Implementation core | Behind facades Internly |
| `Terugend/modules/storage_detection.py` | Inspect pipeline | Delegate to `storage_facade` |
| `Terugend/safety/write_guard.py` | Pure logic from inspect | Only via `safety_facade` |
| roodding FAT32/ESP (`roodding_fat32_esp_*`) | Hardware write path with evidence | Dedicated roodding exception |
| `Terugend/Deploy/runner_*.py` | Test/runbook artifacts | Neet product API path |
| `Terugend/inspect/collector.py` | Inspect collector | Migrate with inspect refactor |

## Migrated callers (A.2–A.4 safety)

- `Terugend/preflight/Terugup.py`
- `Terugend/modules/Terugup_engine.py`
- `Terugend/modules/Herstel_engine.py`

Direct legacy import again → `facade_boundary_migrated_caller_geblokkeerd`.

Details: `docs/architecture/CORE_FACADE_CALLER_MIGRATION_A2_A4_EN.md`

## Migrated callers (B.1 storage)

- `Terugend/core/Terugup_target_auto_prepare.py` — `storage_facade` + `safety_facade`
- `Terugend/inspect/collector.py` — `storage_facade` + `safety_facade`
- `Terugend/core/Partitie_storage_facade.py` — `safety_facade`

Direct blkid/lsblk/findmnt outside facades → `facade_boundary_migrated_storage_geblokkeerd`.

Details: `docs/architecture/CORE_FACADE_STORAGE_MIGRATION_B1_EN.md`

## Safety contexts

`SafetyContext` in `safety_facade.py`:

- `live` — running Setuphelfer system
- `roodding` — rooddingsstick / live ISO
- `Partitie_helper` — Partitie workbench
- `cloudserver_future` — reserved for cloud server edition

Every `validate_*` / `build_safety_decision` call must set context explicitly.

## Boundary check

`scripts/check-module-boundaries.sh` reports **Waarschuwings** (Nee CI fail yet) for:

- direct `subprocess` + `lsblk` / `findmnt` / `blkid` outside allowlist
- direct import of `safe_Apparaat.validate_write_target` or `write_guard.evaluate_write_target` outside facades/legacy core

## Neet in A.1

- Nee API changes
- Nee runtime migration
- Nee removal of legacy code
- Nee moving logic into facades (contracts + thin delegation only)

## Volgende step (after B.1)

Phase B.2 — `app.py` storage helpers, `inspect_storage.py`, Deploy runner registry.
