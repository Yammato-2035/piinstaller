# QEMU 212528 — Fix Presence Review (886a098)

**Datum:** 2026-06-03

## Backend `/opt`

| Check | Wert |
|-------|------|
| `10.0.2.2` in `_get_allowed_hosts()` | **yes** (`/opt/setuphelfer/backend/app.py:2906`) |
| Backend-Fix live | **yes** (Operator-Deploy vor QEMU-Lauf) |

## Build-Tree / ISO

| Check | Wert |
|-------|------|
| PYTHONPATH `/backend:/opt/setuphelfer-rescue` im Tree | **yes** |
| `python3 -m devserver_agent.cli` (subprocess in Autopilot) | **yes** |
| Host-Header `Host: 127.0.0.1:8000` | **yes** |
| ISO SHA256 (Smoke) | `bae2be321e81c0df68df863e89851a10ede9d1ca80ab2812b5e1f03780af0e61` |
| Build run_id | `rescue_developer_iso_20260603_212149` (LB_EXIT=0, 21:21–21:25) |
| Squashfs-Inhalt geprüft | **yes** — Fix-Marker in `filesystem.squashfs` |

## ISO-Validator

| Feld | Wert |
|-------|------|
| `validate_iso_exit` | **21** (`RESCUE-QEMU-AUTOPILOT-CALL-001`) |
| Bewertung | **review_required** — Squashfs enthält Fix; Validator-Regex erwartet Shell-Muster `python3 -m devserver_agent.cli`, Autopilot nutzt Python-`subprocess`-Liste → **False-Negative** |

## QEMU-Lauf vs. Fix-Stand

**`qemu_ran_against_fixed_iso_but_failed`**

Operator hat nach Strict-Block deployt, ISO neu gebaut (developer-qemu), dann QEMU `212528` unter `local_lab`-Preflight gestartet. **Nicht** alter ISO-/Opt-Stand wie Run `111427`.

## Status

`qemu_ran_against_fixed_iso_but_failed`
