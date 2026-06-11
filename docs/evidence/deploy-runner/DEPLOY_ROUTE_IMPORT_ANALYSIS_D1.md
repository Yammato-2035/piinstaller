# Deploy Route Import Analysis (Phase D.1)

**Quelle:** `backend/deploy/routes.py` — statisch, HEAD `1b24669`

## Import-Übersicht

| Import-Typ | Anzahl in routes.py | Zentralisierbar? |
|------------|---------------------|------------------|
| `from deploy.runner_*` | **104** | Teilweise — Domain-Router reduzieren pro Datei |
| `from deploy.runner_api_facade` | **1 Block** (11 Symbole) | **Ja** — bleibt kanonisch für Registry/Risk/Plan-only |
| `from deploy.runner_registry` | **0** | Bereits zentralisiert (nur Facade) |
| `from deploy.runner_result_contract` | **0** | Bereits zentralisiert (nur Facade/Runner) |
| `from deploy.runner_risk_gate` | **0** | Bereits zentralisiert (nur Facade) |
| `deploy.*` Core (plan, execute, write, …) | **~25 Module** | Domain `runtime` — bleibt in `routes_runtime.py` |
| `rescue.*` | **~15 Module** | Domain `rescue` — bleibt domain-spezifisch |

## Runner-Import-Verteilung (geschätzt nach Domain)

| Domain | ~Runner-Imports im Handler-Kontext |
|--------|-----------------------------------|
| rescue + rescue_build | ~55 |
| evidence | ~25 |
| versioning | ~15 |
| governance | ~10 |
| diagnostics | ~7 |
| runtime (runner sandbox/audit) | ~12 |
| registry + risk_gate | **0** |

## Zentralisierungsstrategie

### Kann zentral bleiben (Facade)

- `runner_api_facade` — einziger Einstieg für Registry-GET, Risk-Gate-GET, `build_plan_only_response`
- Keine neuen direkten `runner_registry` / `runner_risk_gate` Imports in Subroutern

### Domain-spezifisch bleiben muss

- `runner_rescue_*` → `routes_rescue.py` / `routes_rescue_build.py`
- Core `deploy.execute`, `deploy.write_execute` → `routes_runtime.py`
- `rescue.backup_*`, `rescue.restore_*` → `routes_backup.py`, `routes_restore.py`

### Mittelfristig reduzierbar (C.7+ / D.4+)

- Weitere `allowed_plan_only` POST-Routen → `build_plan_only_response` (Import pro Route entfällt)
- Evidence-Domain: von ~25 auf ~10 Imports nach plan-only-Migration

## Warum keine Big-Bang-Import-Bereinigung?

104 Imports sind funktional, aber nicht strukturell. Physische Aufteilung (D.2+) bringt **pro Datei** überschaubare Import-Listen ohne Verhaltensänderung. Import-Reduktion und Router-Extraktion sind **parallele**, nicht identische Schritte.

## Boundary-Guard

`check-module-boundaries.sh` meldet `routes_direct_runner_import_count:104` (warn-only). Nach D.2/D.3 sinkt die Zeilenzahl in `routes.py`, Import-Count bleibt bis Runner-Migration unverändert.
