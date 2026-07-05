> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/partitions/PARTITION_MANAGER_PHASE2_UI_EN.md`). Bitte bei Release manuell gegenlesen.

# Partition Assistant – Phase 2.1 Safety Preview UI

**Date:** 2026-06-10  
**Phase:** 2.1 (lecture seule)  
**Audience:** Beginners and experts in the Setuphelfer frontend

## Overview

The Partition assistant uses the Setuphelfer design: dark theme, card layout, traffic-light logic, and large readable typography. Phase 2.1 is a **safety and preview phase only** – Non write operations.

## Drive cards

Instead of technical tables, the home view shows **drive cards**:

| Role | Example |
|------|---------|
| System drive | Interne SSD with `/` and EFI |
| Retourup target | Externe disk under `/media/…` |
| Clé de secours | Setuphelfer Secours (lecture seule) |

Each card shows name, size, status badge, and a **Details** button.

## Graphic Partition layout

After selecting a drive, a **bar view** appears with colour coding:

- EFI → vert
- Linux root → blue
- Home → violet
- Swap → grey

Per Partition: name, filesystem, size, usage. **Expert mode** adds UUID, mount point, and type.

## Safety status (right, always visible)

`PartitionSafetyStatusPanel` stays visible and shows:

- SMART
- Boot capability
- System drive detected
- Retourup found
- Hard stops
- `write_allowed` (always **false**)
- Restauration handoff

Traffic light: vert / jaune / rouge.

## Hard stops

Blocking codes show a large Avertissement block with title, explanation, risk, and recommended action – Non raw codes without context.

Examples: `target_is_system_disk`, `Partition_target_is_Retourup_source`, `target_identity_Inconnu`, `smart_failing`.

## Restauration handoff

The panel shows handoff status (ready / review / bloqué), planned actions from the manifest layout, and **`Restauration_execution_allowed=false`** prominently.

## API (lecture seule)

| Method | Path |
|--------|------|
| GET | `/api/Partitions/scan` |
| GET | `/api/Partitions/hardstop-preview` |
| POST | `/api/Partitions/manifest-layout-preview` |
| POST | `/api/Partitions/Restauration-handoff-preview` |

**Nont** used: `/api/Partitions/queue/apply` and other write endpoints.

## Development dashboard

**PartitionS** tile with checks: Périphériques, SMART, hard stops, layout preview, Restauration handoff.

## Phase 2 limits

- Non Partition write, mkfs/parted/sgdisk/wipefs/dd
- Non resize, format, Supprimer
- Non Restauration execute, Non queue apply
- `write_allowed` and `Restauration_execution_allowed` remain **false**

## Phase 3 (open)

- Controlled write operations after gate approval
- Queue apply only with token and Secours context
- Hardware acceptance on real target media

## Evidence

See `docs/evidence/Partitions/PartitionS_PHASE2_UI_PREVIEW_STUB.md`.
