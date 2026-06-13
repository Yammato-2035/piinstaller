# R.4 Phase 0 — Repo- und Gate-Status

**Kampagne:** R.4 Browser/Display/Kiosk/GRUB/Telemetrie-Spool  
**Datum:** 2026-06-10  
**HEAD:** `185d4a7` (nach R.3-Commit)  
**Branch:** `main`  
**Version (Workspace):** `1.7.17.0` (vorbereitet, nicht committed)

## Dirty Tree

Ja — viele fremde Änderungen unverändert. R.4 bearbeitet nur Build-Konfiguration, Skripte, Core-Tests und Doku.

## Gates

| Gate | Ergebnis |
|------|----------|
| `check-module-boundaries.sh` | `review_required` |
| `check-runtime-deploy-gate.sh` | Exit **20** (`LEGACY_GATE_NON_PROFILE_AWARE`) |

## R.4 Scope

- Kein ISO-Build, kein USB-Write, kein Hardwaretest
- Kein Deploy, Backup, Restore, apt install, systemctl restart

## Referenz

`docs/evidence/rescue/CAMPAIGN_R4_PROMPT.md` — Ziele und R.5-Übergang dokumentiert.
