# Rescue UI Smoke Gate — Spezifikation (2026-06-24)

## Zweck

**Blocker vor jedem Payload-/SquashFS-Build:** Wenn die UI-Basis im Workspace fehlschlägt, dürfen Repack, Stick-Update und produktive Hardware-Tests nicht starten.

## Ausführung

```bash
./scripts/check-rescue-ui-smoke-gate.sh
# oder explizit:
cd backend && ./venv/bin/python -m pytest tests/test_rescue_ui_smoke_gate_v1.py -q
```

Der Repack-Script `scripts/rescue-live/repack-rescue-squashfs-react-shell.sh` ruft dieses Gate **vor** `build-rescue-react-ui.sh` auf.

## Pflichtkriterien (alle müssen GRÜN sein)

| ID | Kriterium | Prüfmethode |
|----|-----------|-------------|
| SG-01 | Toolbar sichtbar (CSS + Shell) | Statisch: `.rescue-toolbar`, `RescueShellLayout` |
| SG-02 | Shutdown sichtbar | `RescuePowerButton`, `data-rescue-shutdown` |
| SG-03 | Sprachauswahl sichtbar | `RescueLanguageSelect` in Toolbar |
| SG-04 | Logo sichtbar (Dashboard) | `data-rescue-logo`, `rescue-brand-row` |
| SG-05 | Dashboard sichtbar | `RescueDashboard`, `data-rescue-tiles` |
| SG-06 | Tiles sichtbar | `RESCUE_NAV_TILES`, ≥9 Tiles |
| SG-07 | Tiles klickbar (Routing) | `onSelectTile` in `RescueApp` |
| SG-08 | Kein Full-Width-Layout | CSS `max-width: 520px` auf Tiles, Grid max 1100px |
| SG-09 | Safe-Walk aktivierbar | `rescueSafeMode.ts`, `safe_walk` / `RESCUE_UI_SAFE_WALK` |
| SG-10 | Screenshot API vorhanden | Route `/api/rescue/ui/screenshot`, Core-Modul |
| SG-11 | Capabilities API | `GET /api/rescue/ui/screenshot/capabilities` |

## Build-Regel

| Gate-Ergebnis | Payload-Build | SquashFS-Repack | Stick-Update |
|---------------|---------------|-----------------|--------------|
| **GRÜN** (Exit 0) | erlaubt | erlaubt | erlaubt (Operator) |
| **ROT** (Exit ≠ 0) | **VERBOTEN** | **VERBOTEN** | **VERBOTEN** |

## Keine destruktiven Aktionen

Smoke Gate prüft **nur** Quellcode, CSS und API-Verträge — kein Backup, Restore, Shutdown, Partitionieren, USB-Write.

## Referenzen

- Test: `backend/tests/test_rescue_ui_smoke_gate_v1.py`
- Skript: `scripts/check-rescue-ui-smoke-gate.sh`
- MSI Live: `docs/evidence/msi/MSI_UI_SAFE_WALK_CHECKLIST_2026-06-24.md`
