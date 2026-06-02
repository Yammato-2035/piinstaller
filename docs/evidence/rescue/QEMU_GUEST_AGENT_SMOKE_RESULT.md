# QEMU Guest Agent Smoke — Ergebnis

**Stand:** 2026-06-02 (Operator-Ingest)  
**HEAD:** `9607b63`  
**Run-ID:** `qemu_rescue_developer_autopilot_20260602_202725`  
**Status:** **`blocked`**

## Operator-Smoke durchgeführt

| Feld | Wert |
|------|------|
| local_lab während Smoke | **yes** |
| Proxy 8001 | **yes** |
| KVM | **yes** |
| QEMU Exit | **124** (1200s Timeout) |
| Serial | **0 Bytes** |
| guest_found / report_new | **false / false** |
| release restored | **yes** |

## Root Cause

**`qemu_serial_capture_failure`** — Standard-Profil-ISO ohne `console=ttyS0` (`quiet splash`); Serial-Capture liefert keine Bootmarker.

Mitursache: **`guest_agent_autostart_gap`** — Autopilot- und Dev-Agent-Units nicht in `multi-user.target.wants`.

## Guardrails

Kein Host-Disk, kein USB, kein Restore, kein Backup. Kein neuer QEMU in diesem Ingest.

## Nächster Schritt

ISO mit **`developer-qemu`**-Profil rebuilden (Serial + Autopilot-Enable) oder bootappend/enable fixen — dann erneuter Operator-QEMU-Smoke.

Rescue-Stick bleibt **nicht grün** ohne Boot-/Agent-Nachweis.

JSON: `qemu_guest_agent_smoke_latest.json`  
Details: `QEMU_GUEST_AGENT_FAILURE_CLASSIFICATION.md`
