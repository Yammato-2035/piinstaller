# Deploy Legacy Identifier Hotspot Analysis (DE)

Read-only Auswertung verbleibender aktiver Legacy-Identifier aus:

- `docs/evidence/runtime-results/handoff/legacy_identifier_inventory.json`
- optional `setuphelfer_identifier_cleanup_cycle_1_postcheck.json`
- optional `setuphelfer_identifier_consistency_check.json`

Ergebnis: `docs/evidence/runtime-results/handoff/legacy_identifier_hotspot_analysis.json` (Cluster, Kritikalitaet, Top-Hotspots, priorisierte Cleanup-Ziele).

Keine Quellcode-Aenderungen, keine Runtime, keine Services, Version bleibt 1.7.0.

API: `POST /api/deploy/legacy-identifier-hotspot-analysis` mit `explicit_overwrite`.

Codes: `DEPLOY_LEGACY_IDENTIFIER_HOTSPOT_ANALYSIS_OK`, `DEPLOY_LEGACY_IDENTIFIER_HOTSPOT_ANALYSIS_REVIEW_REQUIRED`, `DEPLOY_LEGACY_IDENTIFIER_HOTSPOT_ANALYSIS_BLOCKED`.

## FAQ (Kurz)

- **Warum Hotspot-Analysen?** Sie buendeln Treffer nach Wirkungsort (Backend, Tauri, ENV, Skripte, …) statt nur zu zaehlen.
- **Warum sind Runtime-Identifier kritischer als Kommentare?** Sie wirken zur Laufzeit (Pfade, Units, ENV, API); Kommentare sind i. d. R. dokumentarisch.
- **Warum loest „unknown“ `review_required` aus?** Ohne klare Einordnung ist das Risiko nicht bewertbar.
- **Warum Tests zuletzt?** Produktiver Code, Startpfade und Packaging haben Vorrang vor Testartefakten.
