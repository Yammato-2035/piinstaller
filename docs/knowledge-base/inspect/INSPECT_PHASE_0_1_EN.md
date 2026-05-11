# Knowledge Base: Inspect Phase 0/1 (EN)

## Defensive analysis

Inspect phase 0/1 is a defensive analysis layer for later rescue/deploy workflows.
The focus is stable data collection and reproducible machine-readable codes.

## No write operations

- no write mounts or repair actions
- no restore actions
- no deploy actions
- no partition-table modifications

## Data sources

- `modules.storage_detection.*`
- `modules.inspect_storage.*`
- `modules.inspect_boot.analyze_boot_status`
- `modules.rescue_readonly_analyze._analyze_network`

## Preparation for rescue/deploy

Inspect provides preparatory raw data and hint flags (`capabilities.os_hints`), but no release decisions.
Release decisions remain in later phases with explicit safety gates.
