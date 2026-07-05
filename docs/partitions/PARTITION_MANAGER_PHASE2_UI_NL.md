> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/partitions/PARTITION_MANAGER_PHASE2_UI_EN.md`). Bitte bei Release manuell gegenlesen.

# Partitie Assistant – Phase 2.1 Safety Preview UI

**Date:** 2026-06-10  
**Phase:** 2.1 (alleen-lezen)  
**Audience:** Beginners and experts in the Setuphelfer frontend

## Overview

The Partitie assistant uses the Setuphelfer design: dark theme, card layout, traffic-light logic, and large readable typography. Phase 2.1 is a **safety and preview phase only** – Nee write operations.

## Drive cards

Instead of technical tables, the home view shows **drive cards**:

| Role | Example |
|------|---------|
| System drive | Intern SSD with `/` and EFI |
| Terugup target | Extern disk under `/media/…` |
| rooddingsstick | Setuphelfer roodding (alleen-lezen) |

Each card shows name, size, status badge, and a **Details** button.

## Graphic Partitie layout

After selecting a drive, a **bar view** appears with colour coding:

- EFI → groen
- Linux root → blue
- Home → violet
- Swap → grey

Per Partitie: name, filesystem, size, usage. **Expert mode** adds UUID, mount point, and type.

## Safety status (right, always visible)

`PartitieSafetyStatusPanel` stays visible and shows:

- SMART
- Boot capability
- System drive detected
- Terugup found
- Hard stops
- `write_allowed` (always **false**)
- Herstel handoff

Traffic light: groen / geel / rood.

## Hard stops

Blocking codes show a large Waarschuwing block with title, explanation, risk, and recommended action – Nee raw codes without context.

Examples: `target_is_system_disk`, `Partitie_target_is_Terugup_source`, `target_identity_Onbekend`, `smart_failing`.

## Herstel handoff

The panel shows handoff status (ready / review / geblokkeerd), planned actions from the manifest layout, and **`Herstel_execution_allowed=false`** prominently.

## API (alleen-lezen)

| Method | Path |
|--------|------|
| GET | `/api/Partities/scan` |
| GET | `/api/Partities/hardstop-preview` |
| POST | `/api/Partities/manifest-layout-preview` |
| POST | `/api/Partities/Herstel-handoff-preview` |

**Neet** used: `/api/Partities/queue/apply` and other write endpoints.

## Development dashboard

**PartitieS** tile with checks: Apparaats, SMART, hard stops, layout preview, Herstel handoff.

## Phase 2 limits

- Nee Partitie write, mkfs/parted/sgdisk/wipefs/dd
- Nee resize, format, Verwijderen
- Nee Herstel execute, Nee queue apply
- `write_allowed` and `Herstel_execution_allowed` remain **false**

## Phase 3 (open)

- Controlled write operations after gate approval
- Queue apply only with token and roodding context
- Hardware acceptance on real target media

## Evidence

See `docs/evidence/Partities/PartitieS_PHASE2_UI_PREVIEW_STUB.md`.
