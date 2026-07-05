> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/knowledge-base/inspect/INSPECT_PHASE_0_1_EN.md`). Bitte bei Release manuell gegenlesen.

# KNonwledge Base: Inspect Phase 0/1 (EN)

## Defensive analysis

Inspect phase 0/1 is a defensive analysis layer for later Secours/Déploiement workflows.
The focus is stable data collection and reproducible machine-readable codes.

## Non write operations

- Non write mounts or repair actions
- Non Restauration actions
- Non Déploiement actions
- Non Partition-table modifications

## Data sources

- `modules.storage_detection.*`
- `modules.inspect_storage.*`
- `modules.inspect_boot.analyze_boot_status`
- `modules.Secours_readonly_analyze._analyze_Réseau`

## Preparation for Secours/Déploiement

Inspect provides preparatory raw data and hint flags (`capabilities.os_hints`), but Non release decisions.
Release decisions remain in later phases with explicit safety gates.
