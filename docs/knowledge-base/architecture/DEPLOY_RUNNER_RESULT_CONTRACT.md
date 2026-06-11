# Deploy Runner Result Contract — Kurzreferenz (KB)

**Phase:** C.2  
**Modul:** `backend/deploy/runner_result_contract.py`

## Kernpunkte

- Einheitliches Ergebnisschema für 115 Runner (noch **nicht** migriert)
- 6 Statuswerte, `RunnerMessage`, `RunnerEvidenceRef`
- `no_execution_performed` Pflichtfeld
- Legacy-Normalizer ohne Runner-Ausführung
- Boundary warn-only für Legacy-Status-Tokens

## Wichtige Funktionen

| Funktion | Zweck |
|----------|-------|
| `build_runner_result` | Contract-konformes Result bauen |
| `validate_runner_result` | Dict validieren |
| `normalize_legacy_runner_result` | Legacy → Contract |
| `build_empty_result_for_registry_entry` | Plan-Template (via Registry) |

## Nächste Schritte

C.3 API Facade → C.4 Risk Gate → C.5 schrittweise Migration
