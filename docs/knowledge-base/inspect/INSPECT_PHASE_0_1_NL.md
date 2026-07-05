> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/knowledge-base/inspect/INSPECT_PHASE_0_1_EN.md`). Bitte bei Release manuell gegenlesen.

# KNeewledge Base: Inspect Phase 0/1 (EN)

## Defensive analysis

Inspect phase 0/1 is a defensive analysis layer for later roodding/Deploy workflows.
The focus is stable data collection and reproducible machine-readable codes.

## Nee write operations

- Nee write mounts or repair actions
- Nee Herstel actions
- Nee Deploy actions
- Nee Partitie-table modifications

## Data sources

- `modules.storage_detection.*`
- `modules.inspect_storage.*`
- `modules.inspect_boot.analyze_boot_status`
- `modules.roodding_readonly_analyze._analyze_Netwerk`

## Preparation for roodding/Deploy

Inspect provides preparatory raw data and hint flags (`capabilities.os_hints`), but Nee release decisions.
Release decisions remain in later phases with explicit safety gates.
