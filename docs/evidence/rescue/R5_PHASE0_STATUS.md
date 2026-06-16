# R.5 Phase 0 — Repo-Status und Ausgangslage

**Kampagne:** R.5 Controlled ISO Build + Stick Write + MSI Boot Test  
**Datum:** 2026-06-10  
**Branch:** `main`  
**HEAD:** `57e30d9`  
**Version:** `1.7.17.0`

## Dirty Tree

Ja — viele fremde Änderungen (Frontend, DCC-Evidence, Payload-Fix, Submodule). R.5 berührt nur Evidence-Doku und read-only Prüfungen.

## Gates

| Gate | Ergebnis |
|------|----------|
| `check-module-boundaries.sh` | `review_required` |
| `check-runtime-deploy-gate.sh` | Exit **20** (`LEGACY_GATE_NON_PROFILE_AWARE`) |

## Operator-Gates (Umgebung)

| Gate | Wert | Status |
|------|------|--------|
| `OPERATOR_ISO_BUILD_FREIGABE` | **0** | nicht gesetzt → kein ISO-Build |
| `OPERATOR_USB_WRITE_FREIGABE` | **0** | nicht gesetzt → kein USB-Write |
| `USB_TARGET` | *(leer)* | nicht gesetzt |

## Voraussetzungen

| Prüfung | Status |
|---------|--------|
| R.4-Commit vorhanden | **ja** (`57e30d9 feat(rescue): prepare browser kiosk and boot verification`) |
| R.3-Persistenzmodule | **ja** (`rescue_persistence.py`, `rescue_boot_logger.py`, …) |
| R.4 Browser/Kiosk-Dateien | **ja** (package-list, kiosk-skripte, openbox autostart, matrix v4) |

## Vorhandene ISO (read-only Hinweis)

`binary.hybrid.iso` existiert (652M, **2026-06-07**) — **vor R.4**, ohne Kiosk/Browser-Stack im SquashFS. Für R.5-Abnahme **nicht verwendbar** ohne neuen Build (Gate A).

## Nächster Schritt

Phase 1 Build-Config → Phase 2 Preflight → Gate A für Controlled Build.
