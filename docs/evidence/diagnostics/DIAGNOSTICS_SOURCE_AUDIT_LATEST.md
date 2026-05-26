# Diagnostics Source Audit (Latest)

- **Generated at:** `2026-05-26T21:45:29Z`
- **Project version:** `1.7.2`
- **Source commit:** `9ad7477`
- **Scope:** read-only audit of `backend/core/diagnostics/`, diagnostics API routes/tests, dev-dashboard roadmap UI, rescue runtime evidence, roadmap registry, and notification/provider-limit evidence.

## Vorhandene Diagnostik-Komponenten

- Katalog / Modelle / Matcher: `backend/core/diagnostics/registry.py`, `models.py`, `matcher.py`, `runner.py`, `evidence_store.py`
- API-Endpunkte: `POST /api/diagnostics/analyze`, `GET /api/diagnostics/catalog`, `GET /api/diagnostics/{id}`, `GET /api/diagnostics/evidence/schema`, `GET /api/diagnostics/evidence/sample`
- Vorhandene UI-Anbindung:
  - `frontend/src/components/DiagnosticsAssistantPanel.tsx`
  - `frontend/src/components/dev-dashboard/RoadmapDrawer.tsx`
  - `frontend/src/components/dev-dashboard/RoadmapDrawer.test.ts`
- Vorhandene Evidence / Laufzeitquellen:
  - `docs/evidence/runtime-results/rescue/rescue_build_diagnostics_mapping_latest.json`
  - `docs/evidence/runtime-results/rescue/rescue_build_next_steps_matrix_latest.json`
  - `docs/evidence/dev-dashboard/NOTIFICATION_MODULE_INTEGRATION_RESULT.md`
  - `docs/evidence/runtime-results/notifications/notification_events.jsonl`
  - `data/diagnostics/evidence/*.json`

## Vorhandene Katalog-/Matcher-Dateien

- `registry.py` enthält bereits Backup-, Restore-, Runtime-, Service-Conflict- und erste Rescue-Build-Cases.
- Vor diesem Lauf waren `RESCUE-BUILD-ROOT-001`, `RESCUE-BUILD-GATE-001` und `RESCUE-BUILD-ARCH-001` vorhanden.
- In diesem Lauf ergänzt: `RESCUE-BUILD-TOOL-001`, `RESCUE-BUILD-RSVG-001`, `NOTIFICATION-EMAIL-PROVIDER-001`.

## Vorhandene API-Endpunkte

- Diagnostics-API ist vorhanden und read-only.
- Developer-Dashboard-Status liefert Roadmap-/Registry-Daten, bisher aber ohne feingranulare `diagnostics_progress`-Auswertung.
- In diesem Lauf wurde die sichtbare Teilfortschrittsstruktur über die Roadmap-/Dashboard-Schicht ergänzt.

## Vorhandene UI-Anbindung

- Die generische Diagnostics-UI (`DiagnosticsAssistantPanel`) existiert bereits.
- Die Roadmap-/Next-Prompt-Ansicht hatte bislang nur einen allgemeinen Diagnostics-Hinweis.
- In diesem Lauf ergänzt: sichtbares Diagnostics-Fortschrittsgrid, gelernte Diagnosecodes, Evidence-Dateien und nächster Testfokus im Development Dashboard.

## Vorhandene Evidence

- Rescue-Build- und Architektur-Evidence ist bereits reichlich vorhanden.
- Notification-Provider-Limit ist bereits fachlich belegt, war aber noch nicht als Diagnosecode im Katalog verankert.
- Für diesen Lauf neu: dedizierte Diagnostics-Evidence-Dateien unter `docs/evidence/diagnostics/`.

## Bekannte Lücken

- Backup-/Runtime-/Deploy-spezifische Diagnosecodes sind noch nicht vollständig als eigener Katalogtrack modelliert; die Teststrecke dokumentiert diese Fälle deshalb teilweise mit symbolischen Codes.
- Restore-Diagnostik bleibt fachlich sichtbar, aber echte Restore-E2E-Ausführung bleibt weiter `deferred`.
- Diagnostics bleibt bewusst **nicht grün**, solange die vollständige reproduzierbare Matrix fehlt.

## Vorhandene Rescue-Build-Erkenntnisse

- Root-/TTY-/Operator-Policy-Blocker
- kontrolliertes `lb build`-Gate (Exit 20)
- fehlende Host-Abhängigkeit `librsvg2-bin` / `rsvg-convert`
- Legacy-`rsvg`-Erwartung von `live-build`
- Architekturtrennung `amd64` / `i386` / `arm64` / `armhf`

## Fehlende Rescue-Build-Erkenntnisse

- echter erfolgreicher Operator-Terminal-Build
- ISO-Artefakt-Verifikation
- Boot-/USB-/Hardware-Nachweis

## Status je Teilbereich

- `catalog`: `partial_green`
- `matcher`: `partial_green`
- `api`: `partial_green`
- `ui`: `partial_green`
- `evidence`: `partial_green`
- `tests`: `partial_green`
- `kb`: `partial_green`
- `i18n`: `partial_green`

## Fazit

Diagnostics ist jetzt deutlich erklärbarer und reproduzierbarer, aber weiterhin nur `partial_green`: Wiederkehrende Rescue-/Notification-Fehler sind in Katalog, Matcher, Teststrecke, Dashboard-Auswertung und Evidence gespiegelt. Full green bleibt bis zur vollständigen Matrix bewusst blockiert.
