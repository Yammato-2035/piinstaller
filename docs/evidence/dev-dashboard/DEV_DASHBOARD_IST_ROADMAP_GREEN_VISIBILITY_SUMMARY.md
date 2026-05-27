# Dev Dashboard — IST, Roadmap-Sichtbarkeit, Green Visibility (Summary)

**Datum:** 2026-05-27

## Kurzfassung

- **Phase-0:** Gate Exit **0** — Live-API ausgewertet.
- **Roadmap-Ursache:** `ExternalDevelopmentControlCenter` (Cockpit) hatte **keinen** `RoadmapDrawer`; API lieferte Daten, UI zeigte sie dort nicht.
- **Fix (Workspace):** Roadmap im Cockpit, Datenquellen-Banner, Snapshot-`areas[]`, grüne Gates deutlicher — **ohne** Fake-Green und **ohne** Deploy in diesem Lauf.
- **Live-Sichtbarkeit Cockpit:** erst nach **Frontend-Deploy** (nicht in diesem Auftrag).

## Evidence-Index

| Datei | Inhalt |
|-------|--------|
| `current_dashboard_ist_stand_latest.md` / `.json` | IST-Stand Live vs Workspace |
| `ROADMAP_VISIBILITY_AUDIT.md` / `roadmap_visibility_audit_latest.json` | Root-Cause-Analyse |
| `LOW_EFFORT_GREEN_CANDIDATES.md` / `.json` | Aufwand/Risiko-Matrix |
| `GREEN_STATUS_VISIBILITY_IMPROVEMENT.md` | Darstellungs-Fix ohne Logikänderung |
| `dev_dashboard_ist_roadmap_green_visibility_summary_latest.json` | Maschinenlesbare Zusammenfassung |

## Nächster Prompt

`RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD` (nach optionalem Frontend-Deploy für Cockpit-Roadmap).
