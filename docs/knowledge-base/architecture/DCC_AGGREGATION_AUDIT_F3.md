# KB: DCC Aggregation Audit F.3

Kurzfassung für Operatoren und Entwickler.

## Was wurde geprüft?

Nach F.1 (Facade) und F.2 (6 Router-Migrationen) wurde **ohne Code-Änderung** analysiert:

- verbleibende Direktzugriffe auf DCC-Core
- doppelte Ampel-/Status-Logik
- Roadmap-Subrouter-Grenze
- AI-Prompt-Stub
- Deploy/Core-Kopplung

## Wichtigste Erkenntnisse

1. **`dcc_status_facade`** bleibt einziger HTTP-Aggregations-Einstieg für migrierte Routen.
2. **`POST /api/ai/prompt/generate`** soll in F.4 dieselbe Facade wie `GET cursor-meta-prompt` nutzen.
3. **Roadmap-Subroutes** (`/roadmap/areas`, …) dürfen `load_roadmap_registry_bundle` direkt aufrufen — reine Registry-Slices.
4. **`deploy_job_state`** liest noch direkt `build_dashboard_status` — mittelfristig Facade-Hook.
5. **Frontend** hat noch keine zentrale `dccStatusViewModel` — Duplikat-Risiko mit Backend-Mappings.

## Nächste sichere Migration

**F.4:** `ai_prompt_generate_stub` → `build_dcc_cursor_meta_prompt_api()`

Vollständig: [DCC_AGGREGATION_AUDIT_F3.md](../../architecture/DCC_AGGREGATION_AUDIT_F3.md)
