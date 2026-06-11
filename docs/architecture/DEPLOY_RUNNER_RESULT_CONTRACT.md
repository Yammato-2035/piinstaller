# Deploy Runner Result Contract (Phase C.2)

**Modul:** `backend/deploy/runner_result_contract.py`  
**Contract-Version:** `CONTRACT_VERSION = 1`  
**Voraussetzung:** C.1 Registry (`runner_registry.py`)

## Warum ein Result Contract?

115 Deploy-Runner liefern heute **14+** verschiedene Status-Literale und uneinheitliche Dict-Strukturen (`errors`, `evidence_files`, verschachtelte `file_results`). Dashboard, DCC und spätere Automation können Ergebnisse nicht zuverlässig aggregieren.

C.2 definiert ein **einheitliches Ergebnisschema** — ohne Runner auszuführen oder zu migrieren.

## Statuswerte (`RunnerResultStatus`)

| Status | Bedeutung |
|--------|-----------|
| `ok` | Erfolg / Gate bestanden |
| `review_required` | Manuelle Prüfung nötig |
| `blocked` | Hart blockiert (mit `errors`) |
| `failed` | Fehlgeschlagen (mit `errors`) |
| `skipped` | Bewusst übersprungen |
| `not_applicable` | Nicht anwendbar |

`unknown` ist **nur** als `kind` erlaubt, **nicht** als `status`.

## Fehler- und Warnungsstruktur

`RunnerMessage`: `{ code, message, severity }` mit `RunnerResultSeverity` (`info`, `warning`, `error`, `critical`).

Regeln:

- `blocked` / `failed` → mindestens ein `errors`-Eintrag
- `review_required` → mindestens `warnings` oder `errors`
- Keine Secrets in `metadata` (Keys wie `password`, `token`)

## Evidence-Pfade

`RunnerEvidenceRef`: `{ path, read_only?, label? }`

- Relativ zum Workspace bevorzugt (`docs/evidence/...`)
- Absolute Pfade nur mit `read_only: true`
- Verboten: `.env`, `/etc/shadow`, Credential-Pfade

## `no_execution_performed`

Pflichtfeld (`bool`). `true` wenn nur Plan, Template oder statische Analyse — trennt C.2-Vorbereitung von echter Laufzeit-Ausführung (C.4 Risk Gate).

## Zusammenhang C.1 Registry

- `build_empty_result_for_registry_entry(entry)` — Plan-Template pro Runner
- `validate_registry_result_contract(entry, result)` — Contract + Registry-Abgleich
- `risk_level` / `execution_policy` aus Registry-Eintrag übernehmen

## Vorbereitung C.3 / C.4

| Phase | Nutzung |
|-------|---------|
| **C.3 API Facade** | Routen liefern `RunnerResult.to_dict()` |
| **C.4 Risk Gate** | Policy + `no_execution_performed` vor Ausführung |
| **C.5 Migration** | `normalize_legacy_runner_result()` pro Runner schrittweise |

## API

- `build_runner_result(...)`
- `validate_runner_result(dict) -> RunnerResultValidation`
- `normalize_legacy_runner_result(runner_id, raw, registry_entry?)`
- `summarize_runner_results(list)`

## Tests

`backend/tests/test_deploy_runner_result_contract_v1.py`

## Verweise

- EN: `DEPLOY_RUNNER_RESULT_CONTRACT_EN.md`
- Pattern-Audit: `docs/evidence/deploy-runner/RUNNER_RESULT_PATTERN_AUDIT_C2.md`
- Registry: `DEPLOY_RUNNER_REGISTRY.md`
