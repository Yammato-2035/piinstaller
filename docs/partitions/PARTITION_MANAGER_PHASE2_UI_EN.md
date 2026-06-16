# Partition Assistant – Phase 2.1 Safety Preview UI

**Date:** 2026-06-10  
**Phase:** 2.1 (read-only)  
**Audience:** Beginners and experts in the Setuphelfer frontend

## Overview

The partition assistant uses the Setuphelfer design: dark theme, card layout, traffic-light logic, and large readable typography. Phase 2.1 is a **safety and preview phase only** – no write operations.

## Drive cards

Instead of technical tables, the home view shows **drive cards**:

| Role | Example |
|------|---------|
| System drive | Internal SSD with `/` and EFI |
| Backup target | External disk under `/media/…` |
| Rescue stick | Setuphelfer Rescue (read-only) |

Each card shows name, size, status badge, and a **Details** button.

## Graphic partition layout

After selecting a drive, a **bar view** appears with colour coding:

- EFI → green
- Linux root → blue
- Home → violet
- Swap → grey

Per partition: name, filesystem, size, usage. **Expert mode** adds UUID, mount point, and type.

## Safety status (right, always visible)

`PartitionSafetyStatusPanel` stays visible and shows:

- SMART
- Boot capability
- System drive detected
- Backup found
- Hard stops
- `write_allowed` (always **false**)
- Restore handoff

Traffic light: green / yellow / red.

## Hard stops

Blocking codes show a large warning block with title, explanation, risk, and recommended action – no raw codes without context.

Examples: `target_is_system_disk`, `partition_target_is_backup_source`, `target_identity_unknown`, `smart_failing`.

## Restore handoff

The panel shows handoff status (ready / review / blocked), planned actions from the manifest layout, and **`restore_execution_allowed=false`** prominently.

## API (read-only)

| Method | Path |
|--------|------|
| GET | `/api/partitions/scan` |
| GET | `/api/partitions/hardstop-preview` |
| POST | `/api/partitions/manifest-layout-preview` |
| POST | `/api/partitions/restore-handoff-preview` |

**Not** used: `/api/partitions/queue/apply` and other write endpoints.

## Development dashboard

**PARTITIONS** tile with checks: devices, SMART, hard stops, layout preview, restore handoff.

## Phase 2 limits

- No partition write, mkfs/parted/sgdisk/wipefs/dd
- No resize, format, delete
- No restore execute, no queue apply
- `write_allowed` and `restore_execution_allowed` remain **false**

## Phase 3 (open)

- Controlled write operations after gate approval
- Queue apply only with token and rescue context
- Hardware acceptance on real target media

## Evidence

See `docs/evidence/partitions/PARTITIONS_PHASE2_UI_PREVIEW_STUB.md`.
