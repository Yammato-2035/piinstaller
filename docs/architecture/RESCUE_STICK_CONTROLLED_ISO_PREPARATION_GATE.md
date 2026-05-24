# Rescue Stick — Controlled ISO Preparation Gate

**Version:** 1.0  
**real_iso_build_allowed:** `false` (bis separater ISO-Build-Prompt + Operator-Freigabe)

## Zweck

Definiert Voraussetzungen für **ISO-Vorbereitung** — **kein** automatischer ISO-Build bei Erfüllung.

## Gate-Bedingungen

| # | Bedingung | Status (2026-05-24) |
|---|-----------|---------------------|
| 1 | Temp Runtime Bundle validiert | **pass** — Validator Exit 0 |
| 2 | Live-Medium Network Validation green | **fail/review** — Hardware-Live-Boot ausstehend |
| 3 | local_only geprüft | **pass** (Host-Proxy + Skripte) |
| 4 | CDN-frei geprüft | **pass** |
| 5 | keine Auto-Writes | **pass** (Emulation + Skripte) |
| 6 | Monolith-Gate nicht blocked | **pass** — review_required |
| 7 | Debian-Live-Basis entschieden | **pass** — emulation `debian_live` |
| 8 | Paketliste emulation-ready | **pass** |
| 9 | systemd-Service-Preview ready | **pass** |
| 10 | Runtime-Bundle-Manifest (Temp) | **pass** — MANIFEST.json |
| 11 | Evidence vollständig | **review_required** — Live-Result offen |
| 12 | Operator-Freigabe ISO-Build | **fail** — nicht erteilt |

## Gate-Status

**ISO_PREP_REVIEW_REQUIRED**

- Temp-Bundle und Emulation: bereit
- Live-OS Network Validation: offen
- Echter ISO-Build: **blockiert**

## Freigabe-Workflow (später)

1. Live-OS Validation **green** + Evidence committed
2. Operator schriftliche Freigabe ISO-Build
3. Phase 0 Runtime-Gate
4. Separater Prompt „Controlled ISO Build“ — **nicht** dieser Auftrag

## Referenzen

- `RESCUE_BIG_STEP_STATUS_PLAN.md`
- `RESCUE_BUILD_MONOLITH_BOUNDARY_GATE.md`
- `RESCUE_STICK_READONLY_BUILD_GATE.md`
