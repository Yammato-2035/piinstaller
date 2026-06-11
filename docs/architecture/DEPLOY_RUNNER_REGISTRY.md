# Deploy Runner Registry (Phase C.1)

**Stand:** Phase C.1 abgeschlossen  
**Modul:** `backend/deploy/runner_registry.py`  
**Registry-Version:** `REGISTRY_VERSION = 1`

## Warum eine Runner Registry?

Unter `backend/deploy/` liegen **115** `runner_*.py`-Dateien (~37k Zeilen). Sie sind das größte Wartungs- und Skalierungsrisiko im Deployment-Bereich: viele direkte Imports in `routes.py`, uneinheitliche Metadaten, schwer abschätzbare Risiken (USB, ISO, sudo, Evidence).

Phase C.1 inventarisiert und typisiert Runner **ohne** sie zu refaktorieren oder auszuführen. Ziel ist Transparenz und stabile Contracts als Grundlage für spätere Orchestrierung.

## Was wird registriert?

Pro Runner eine statische `RunnerRegistryEntry`:

| Feld | Bedeutung |
|------|-----------|
| `runner_id` | Stabiler ID aus Dateiname (Stem) |
| `path` | Relativer Pfad zu `runner_*.py` |
| `category` | Domänen-Cluster (runtime, rescue_build, …) |
| `risk_level` | Konservative Risikoklasse |
| `execution_policy` | Erlaubte Ausführungsmodi |
| Capability-Flags | `writes_files`, `touches_system_paths`, `uses_sudo`, `uses_device_write`, … |
| `has_tests` | Heuristik: passende Testdatei vorhanden |
| `notes` | z. B. `subprocess`, `mount` |

APIs: `build_runner_registry_from_files()`, `classify_runner_file()`, `build_runner_registry_summary()`, `find_runner_by_id()`, `list_runners_by_category()`, `list_runners_by_risk()`, `registry_policy_warnings()`.

Evidence-Export: `scripts/generate-deploy-runner-registry.py` → `docs/evidence/deploy-runner/runner_registry.generated.json`.

## Was wird noch nicht refaktoriert?

- Keine Verschiebung von Runner-Dateien
- Kein Umbau von Runner-Funktionen
- Kein Lazy-Import in `routes.py`
- Kein `app.py`-Refactoring
- Keine API-Facade (→ C.3)
- Kein Result-Contract (→ C.2)
- Kein Risk Gate zur Laufzeit (→ C.4)

## Warum keine Runner-Ausführung in C.1?

Registry und Classifier lesen nur Dateiinhalte (Textscan + Pfadheuristiken). Es werden **keine** Runner importiert oder aufgerufen — kein Deploy, Backup, Restore, ISO-Build, USB-Write, Hardwaretest.

## Risikoklassen (`RunnerRiskLevel`)

| Level | Bedeutung |
|-------|-----------|
| `read_only` | Analyse/Plan ohne Schreibaktion |
| `template_write` | Vorlagen/Manifeste |
| `evidence_write` | Evidence/Docs unter Workspace |
| `local_runtime_change` | Workspace-/Lab-Pfade |
| `system_change` | mount, apt, /opt, /etc |
| `device_write` | dd, mkfs, wipefs, sgdisk |
| `destructive` | Device-write + hohes Schadenspotenzial |

Bei Unsicherheit wählt der Classifier das **höhere** Risiko.

## Execution Policies (`RunnerExecutionPolicy`)

| Policy | Bedeutung |
|--------|-----------|
| `never_auto` | Destruktiv — nie automatisch |
| `manual_only` | Nur manuell |
| `operator_confirmed` | Operator-Bestätigung |
| `lab_only` | Nur Lab/Entwicklung |
| `disabled` | Deaktiviert |

Destructive Runner erhalten `never_auto`. Sudo ohne Operator-Policy und device_write ohne manual_policy erzeugen **Warnungen** in `check-module-boundaries.sh` (warn-only).

## Boundary Guard (warn-only)

`scripts/check-module-boundaries.sh` prüft:

- `runner_registry_missing` — neue `runner_*.py` ohne Registry-Eintrag
- `runner_device_write_without_manual_policy`
- `runner_sudo_without_operator_policy`
- `runner_destructive_without_never_auto`
- **C.2:** `runner_result_unknown_status_token`, `runner_result_no_errors_for_failed_like`, `runner_result_no_evidence_reference`

Exit **0** mit `status: review_required` — noch keine CI-Blockierung.

## Result Contract (C.2, erledigt)

- Modul: `backend/deploy/runner_result_contract.py`
- `build_empty_result_for_registry_entry(entry)` — Plan-Template pro Runner
- `validate_registry_result_contract(entry, result)`
- Details: `docs/architecture/DEPLOY_RUNNER_RESULT_CONTRACT.md`

## API Facade (C.3, erledigt)

- Modul: `backend/deploy/runner_api_facade.py`
- Read-only GET: `/api/deploy/runners/catalog`, `/summary`, `/policy-warnings`, `/{runner_id}`, `/{runner_id}/empty-result`
- Details: `docs/architecture/DEPLOY_RUNNER_API_FACADE.md`

## Nächste Phasen

| Phase | Inhalt |
|-------|--------|
| **C.4** | Runner Risk Gate — Laufzeit-Policy durchsetzen |
| **C.5** | Schrittweise Runner-Migration auf Contract |

## Tests

`backend/tests/test_deploy_runner_registry_v1.py` — Import ohne Runtime, Heuristiken, Summary, keine Runner-Ausführung.

## Verweise

- Inventar: `docs/evidence/deploy-runner/DEPLOY_RUNNER_INVENTORY.md`
- EN: `docs/architecture/DEPLOY_RUNNER_REGISTRY_EN.md`
- KB: `docs/knowledge-base/architecture/DEPLOY_RUNNER_REGISTRY.md`
