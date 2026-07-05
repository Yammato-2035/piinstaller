# DCC-VIS-001 Baseline

**Datum:** 2026-07-05  
**Workspace (tatsächlich):** `/home/volker/piinstaller`  
**Workspace (Auftrag):** `/home/volker/setuphelfer/piinstaller` (Pfad existiert nicht — Symlink/Clone optional)

## Git

| Feld | Wert |
|------|------|
| Branch (Start) | `cursor/master-phase-rescue-beta-30f2` |
| Feature-Branch | `dcc-vis-001-visible-roadmap-changelog` |
| HEAD (Start) | `ef73216` |

## Teststatus vor Änderung

- `loadDevDashboard.test.ts` — 3 Tests grün
- `governanceMatrix.test.ts` — 2 Tests grün
- Kein `scripts/run-tests.sh` vorhanden

## Erkannte DCC-Probleme (Screenshot)

1. **Developer Token** fehlt/ungültig — Statusroute 404 `DEVELOPER_CAPABILITY_REQUIRED`
2. **API-Erkennung widersprüchlich** — Boot-Diagnose `/api/version` HTTP 200, unten „API OFFLINE“ / `backend_api_unreachable`
3. **Runtime Gate** blockiert (Phase 0 / Standalone)
4. **Standalone-Modus** aktiv bei fehlendem Dev-Dashboard-Zugriff
5. **Roadmap** vorhanden, aber nicht als grafischer Projektfortschritt mit sichtbaren Ergebnissen

## Ziel DCC-VIS-001

Runtime-Status entwirren, Token-UX, sichtbarer Changelog, Workspace-Handoff — ohne Fake-Greens.
