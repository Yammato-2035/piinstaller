# Roadmap Registry Implementation

## Ziel

Im Setuphelfer Development Dashboard wurde eine belastbare read-only Roadmap-/Meilenstein-Registry mit Next-Prompt-Registry und Prompt-Export ergänzt. Die Registry soll Wiederholungen ohne Folgeaktion vermeiden und Status nur anhand belegbarer Quellen anzeigen.

## Geänderte Dateien

- `backend/core/dev_dashboard_roadmap.py`
- `backend/core/dev_dashboard_cockpit.py`
- `backend/app.py`
- `backend/tests/test_dev_dashboard_roadmap_registry_v1.py`
- `frontend/src/components/dev-dashboard/RoadmapDrawer.tsx`
- `frontend/src/components/dev-dashboard/RoadmapDrawer.test.ts`
- `frontend/src/pages/DevelopmentDashboard.tsx`
- `frontend/src/locales/de.json`
- `frontend/src/locales/en.json`
- `docs/roadmap/setuphelfer_roadmap.schema.json`
- `docs/roadmap/setuphelfer_roadmap.json`
- `docs/roadmap/setuphelfer_milestones.json`
- `docs/roadmap/setuphelfer_next_prompts.json`
- `docs/roadmap/PROMPT_EXPORT_TEMPLATE.md`
- `docs/evidence/roadmap/ROADMAP_SOURCE_AUDIT.md`
- `docs/evidence/roadmap/roadmap_registry_latest.json`
- `docs/evidence/roadmap/next_prompt_registry_latest.json`
- `docs/evidence/roadmap/NEXT_PROMPT_SELECTION_LATEST.json`
- `docs/dev-dashboard/ROADMAP_REGISTRY_DE.md`
- `docs/dev-dashboard/ROADMAP_REGISTRY_EN.md`
- `docs/knowledge-base/dev-dashboard/ROADMAP_AND_NEXT_PROMPT_REGISTRY.md`
- `docs/faq/dev_dashboard_roadmap_faq.md`
- `CHANGELOG.md`

## Datenmodell

Die Registry nutzt:

- `areas`
- `milestones`
- `tasks`
- `blockers`
- `decisions`
- `notes`
- `next prompts`

Statuswerte sind auf die freigegebene Liste begrenzt. Evidence-Level ist ebenfalls strikt begrenzt. Die Schema-Datei validiert das Roadmap-Hauptdokument.

## API-Endpunkte

Neu ergänzt:

- `GET /api/dev-dashboard/roadmap`
- `GET /api/dev-dashboard/roadmap/areas`
- `GET /api/dev-dashboard/roadmap/milestones`
- `GET /api/dev-dashboard/roadmap/blockers`
- `GET /api/dev-dashboard/roadmap/decisions`
- `GET /api/dev-dashboard/roadmap/next-prompt`
- `GET /api/dev-dashboard/roadmap/next-prompts`
- `GET /api/dev-dashboard/roadmap/export-next-prompt/{prompt_id}`

Alle Antworten bleiben read-only und markieren `execution_allowed = false`.

## UI-Bereiche

Die bisherige Minimal-Roadmap wurde durch eine Registry-Ansicht ersetzt mit:

- Übersichtskarten
- Baumtabelle für Bereiche, Meilensteine und Aufgaben
- ausklappbaren Detailbereichen
- Restore-Hinweis
- Diagnostics-Hinweis
- Next-Prompt-Kachel mit Anzeigen, Kopieren und Exportieren

Es wurden keine Execute-Buttons ergänzt.

## Restore-Entscheidung

Restore bleibt explizit `deferred`, inklusive klarer DE/EN-Begründung: kein bootfähiges Rettungsmedium und kein nicht-produktives Zielsystem verfügbar.

## Diagnostics-Status

Diagnostics bleibt `partial_green`, weil echte Fehlerfall-Teststrecken, UI-Auswertung und Evidence-Matrix weiterhin fehlen.

## Next-Prompt-Logik

Die Registry modelliert mehrere verfügbare Prompts, markiert genau einen Prompt als `recommended_next` und exportiert dafür einen STRICT-MODE-Text. Aktuell ist `DIAGNOSTICS_TEST_TRACK` der empfohlene nächste Prompt.

## Grenzen

- Die Registry führt keine Runtime-Aktionen aus.
- Sie ersetzt keine echte Hardware-/Restore-/Rescue-Evidence.
- `pytest` war in dieser Umgebung nicht installiert; deshalb wurde der Python-Testpfad mit `unittest` verifiziert.
- Die neue Registry ist im Workspace implementiert; eine produktive Runtime-Abnahme der neuen UI/API war nicht Teil dieses Laufs.

## Tests

- `python3 -m py_compile backend/core/dev_dashboard.py backend/core/dev_dashboard_roadmap.py backend/app.py` → erfolgreich
- `PYTHONPATH=backend python3 -m unittest backend.tests.test_dev_dashboard_roadmap_registry_v1 backend.tests.test_dev_dashboard_v1` → erfolgreich
- `npm run test -- src/components/dev-dashboard/RoadmapDrawer.test.ts` → erfolgreich
- `npm run build` → erfolgreich
- `PYTHONPATH=backend python3 -m pytest ...` → nicht möglich, weil `pytest` lokal nicht installiert war
