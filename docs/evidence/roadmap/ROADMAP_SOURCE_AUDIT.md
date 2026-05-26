# Roadmap Source Audit

## Ziel

Diese Analyse dokumentiert, welche bestehenden Roadmap-, Status- und Evidence-Quellen für die neue Development-Dashboard-Roadmap-Registry belastbar sind und wo Konflikte oder Lücken bestehen.

## Gefundene Roadmap-/Statusquellen

- `docs/roadmap/STATUS_MATRIX.md`
  Operative Ampelquelle für aktuelle Bereiche, aber gemischt aus Produktstatus, Release-Gates, Prompt-Rastern und historischen Kurznotizen.
- `docs/roadmap/MASTER_ROADMAP_2026_2030.md`
  Langfristige Leitplanken; bewusst keine operative Ampelquelle.
- `docs/roadmap/master_roadmap_status.json`
  Nur High-Level-Marker für die Master-Roadmap, nicht für Recovery-Core-Freigaben geeignet.
- `docs/dev-dashboard/modules/backup-restore.json`
  Strukturierte Modulquelle für Backup/Restore.
- `docs/dev-dashboard/modules/diagnostics.json`
  Strukturierte Modulquelle für Diagnostics.
- `docs/dev-dashboard/modules/rescue-stick.json`
  Strukturierte Modulquelle für Rescue Stick.
- `docs/dev-dashboard/modules/frontend-ux.json`
  Strukturierte Modulquelle für Dashboard-/Frontend-Status.
- `backend/core/dev_dashboard_cockpit.py`
  Bisheriger Aggregator für `STATUS_MATRIX.md` und Modul-JSONs.
- `backend/core/dev_dashboard.py`
  Bisheriger Dev-Dashboard-Statusbuilder; Roadmap bislang nur als vereinfachte Tabs.
- `backend/app.py`
  Vorhandene Dev-Dashboard-Routen und read-only Status-Endpunkte.
- `frontend/src/pages/DevelopmentDashboard.tsx`
  Aktuelle Dashboard-Seite mit `Roadmap`-Sektion.
- `frontend/src/components/dev-dashboard/RoadmapDrawer.tsx`
  Bisherige minimale Roadmap-UI.
- `frontend/src/pages/ExternalDevelopmentControlCenter.tsx`
  Governance-/Prompt-Fokus, aber keine belastbare Roadmap-Registry.

## Gefundene Evidence-Quellen

- `docs/evidence/release-gates/backup_restore_release_gate.json`
  Autoritative Quelle für BR-001-OFFLINE als Release-Gate und den Ausschluss von BR-001-LIVE als Release-Retry.
- `docs/evidence/release-gates/apt_update_delivery_gap.json`
  Autoritative Quelle für Packaging-/APT-Update-Blocker.
- `docs/evidence/runtime-results/rescue/rescue_build_diagnostics_mapping_latest.json`
  Beleg für Diagnostics-Mapping im Rescue-Kontext.
- `docs/evidence/runtime-results/rescue/rescue_build_next_steps_matrix_latest.json`
  Beleg für Rescue-/Restore-Folgepfade und Deferred-Tracks.
- `docs/evidence/dev-dashboard/RESCUE_ISO_EXECUTOR_DASHBOARD_INTEGRATION_RESULT.md`
  Belegt produktive Dashboard-Integration des Rescue-ISO-Status.
- `docs/evidence/dev-dashboard/PROJECT_OVERVIEW_DASHBOARD_INTEGRATION_RESULT.md`
  Belegt zusätzliche read-only Dashboard-Bereiche.
- `docs/evidence/runtime-results/handoff/rescue_stick_readonly_build_final_gate.json`
  Belegt Read-only-/Emulationsstand des Rescue-Stick-Buildpfads.
- `docs/testing/HARDWARE_TEST_MATRIX.md`
  Belegbare Quelle für echte zukünftige Teststrecken.
- `docs/knowledge-base/FULL_RESTORE_BOOT_TEST.md`
  Historische Restore-/Boot-Evidence, aber nicht ausreichend als Freigabe für aktuelle reale Restore-E2E-Abnahme im Zielkontext.

## Erkannte Lücken

- Es existierte keine einheitliche Registry, die Bereiche, Meilensteine, Aufgaben, Blocker, Entscheidungen, Notes und Next Prompts in einem prüfbaren Modell zusammenführt.
- Restore war dokumentiert als rot/offen, aber die sachliche Zurückstellung wegen fehlendem bootfähigem Rettungsmedium und fehlendem nicht-produktivem Zielsystem war nicht zentral und prominent im Dashboard abgelegt.
- Diagnostics hatte Struktur- und API-Hinweise, aber keine einheitliche Fortschrittsdarstellung aus Katalog, UI-Auswertung, Evidence-Matrix und reproduzierbarer Teststrecke.
- Der bisherige Prompt-Export war ein Meta-Prompt aus Findings, aber keine auditable Next-Prompt-Registry mit Auswahlregel, Blockern und erwarteten Outputs.
- `HostPilot / Serverguide` hat derzeit keine belastbare operative Statusquelle; dafür ist `unknown` bzw. `review_required` nötig.

## Potenzielle Konflikte zwischen alten und neuen Angaben

- `docs/roadmap/master_roadmap_status.json` meldet `overall_status = green`, obwohl die operative Recovery-/Release-Lage laut `STATUS_MATRIX.md` und Release-Gates klar nicht grün ist.
- `STATUS_MATRIX.md` enthält einzelne grüne Einträge ohne belastbare Evidence-Links; das bestehende Cockpit meldet diese bereits als `green_without_evidence`.
- Öffentliche Statusseiten (`docs/roadmap/PUBLIC_STATUS_PAGE.md`) und operative Matrizen nutzen grobe Farben, aber trennen nicht sauber zwischen `blocked`, `deferred`, `partial_green` und `unknown`.
- Rescue-/Restore-Hinweise sind über Architektur-, KB- und Evidence-Dateien verteilt; ohne Registry drohen wiederholte Feststellungen ohne klaren nächsten Prompt.

## Autoritative Quellen für die neue Registry

1. **Release-/Recovery-Gates**
   - `docs/evidence/release-gates/backup_restore_release_gate.json`
   - `docs/evidence/release-gates/apt_update_delivery_gap.json`
2. **Operative Bereichsquellen**
   - `docs/dev-dashboard/modules/backup-restore.json`
   - `docs/dev-dashboard/modules/diagnostics.json`
   - `docs/dev-dashboard/modules/rescue-stick.json`
3. **Strategische Leitplanken**
   - `docs/roadmap/MASTER_ROADMAP_2026_2030.md`
   - `docs/roadmap/ROADMAP_2026.md`
   - `docs/roadmap/MONOLITH_REFACTOR_PLAN.md`
4. **Rescue-/Diagnostics-Spezifika**
   - `docs/evidence/runtime-results/rescue/rescue_build_diagnostics_mapping_latest.json`
   - `docs/evidence/runtime-results/rescue/rescue_build_next_steps_matrix_latest.json`
   - `docs/architecture/RESCUE_OPERATOR_POLICY.md`
   - `docs/architecture/RESCUE_TARGET_ARCHITECTURE_MATRIX.md`
5. **Read-only Runtime Overlay**
   - `GET /api/dev-dashboard/status`
   - `GET /api/version`

## Ableitung für die Registry

- Die neue Registry behandelt `STATUS_MATRIX.md` weiterhin als Hinweisquelle, aber nicht mehr als alleinige operative Wahrheit.
- `green` wird nur gesetzt, wenn Evidence-Level und Statusbegründung das tragen.
- Nicht belegbare Angaben werden als `unknown` oder `review_required` behandelt.
- Der nächste sinnvolle Prompt wird aus dokumentierten Blockern, Evidence-Lücken und Safety-Prioritäten abgeleitet, nicht aus Bauchgefühl.
