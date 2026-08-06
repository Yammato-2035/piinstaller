# 64 GB Carrier Architecture — Rescue Stick

Status: PI-RS-HW-COMPAT-PROVISION-001 (Phase 19), extended by
PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 14).

Languages: [Deutsch](64GB_CARRIER_ARCHITECTURE_DE.md) · [English](64GB_CARRIER_ARCHITECTURE_EN.md) · [Français](64GB_CARRIER_ARCHITECTURE_FR.md) · [Nederlands](64GB_CARRIER_ARCHITECTURE_NL.md)

## Core statement

**A single 64 GB stick cannot hold an unlimited number of full operating
system images.** Setuphelfer therefore uses a catalogue, a bounded cache and
signed images instead of an "everything on the stick" approach.

## Compared variants (`backend/rescue/carrier_layout.py`)

| Variant | Description | Prerequisite |
|---|---|---|
| **A — Universal** | One stick boots natively for both x86_64 and Raspberry Pi | proven, validated shared boot path (currently **does not** exist) |
| **B — Split Carriers** | Shared build catalogue, but separate x86 and ARM/Pi carriers | two physical sticks required |
| **C — Orchestrator Cache** | Universal rescue/orchestrator stick with downloadable/cached target images | default when no universal boot path is proven |

### Decision

Because this repository has **no evidence** for a validated shared boot
sector/ESP path for x86_64 (BIOS/UEFI) **and** Raspberry Pi SD/EEPROM boot,
**variant C (orchestrator cache)** is the specification-compliant default.
`evaluate_carrier_strategy()` marks variant A as `decided` only when a caller
explicitly passes `universal_boot_path_evidence=True` with real evidence.

This is evidence-based interim documentation — not a final product decision.

## Capacity plan (`backend/rescue/carrier_capacity_planner.py`)

The plan uses **actual media bytes**, not a blanket 64 GB assumption. A
safety reserve of **at least 10 %** is planned. Real byte discovery reuses
the existing `storage_facade` — no new `lsblk` logic.

## Possible carrier content (`backend/rescue/carrier_content_catalog.py`)

- Setuphelfer Rescue Runtime
- x86_64 boot path
- optional ARM/Pi boot assets when validated
- hardware catalogue (`data/hardware/`)
- driver/firmware offline packages
- image catalogue (`data/provisioning/os_catalog.json`)
- bounded image cache
- evidence/log area
- update and signature metadata

## Non-goal of this phase

**No partitioning.** `carrier_layout.py` and `carrier_capacity_planner.py`
produce plans/assessments only — no writes to real media.
