# Deploy Route Zielarchitektur (Phase D.1)

**Status:** Planungsdokument — **keine Dateien angelegt**, kein Refactoring in D.1.

## Warum Domain-Aufteilung?

`backend/deploy/routes.py` (5041 Zeilen, 237 Routen, 104 Runner-Imports) ist der größte verbleibende Deploy-Monolith. C.1–C.6 haben Registry, Contract, Facade, Risk Gate und 9 plan-only Routen vorbereitet — die **physische** Router-Aufteilung folgt erst in D.2+.

## Warum kein Big-Bang?

- OpenAPI- und DCC-Clients hängen an stabilen Pfaden unter `/api/deploy/*`
- Execute-/Write-Routen sind CRITICAL — Fehlklassifikation wäre produktionsgefährdend
- Inkrementelle Extraktion mit Facade-Delegation ermöglicht Tests pro Slice ohne Verhaltensänderung

## Vorgeschlagene Zielstruktur

| Zieldatei | Zweck | ~Routen | ~Zeilen | Abhängigkeiten | Risiken |
|-----------|-------|---------|---------|----------------|---------|
| `routes_registry.py` | C.3 GET `/runners/catalog`, `/summary`, `/{id}` | 5 | ~80 | `runner_api_facade` only | **LOW** — reine Facade-Delegation |
| `routes_risk_gate.py` | C.4 GET `/runners/risk-gate/*` | 5 | ~80 | `runner_api_facade` only | **LOW** |
| `routes_evidence.py` | Manual-runtime evidence, lab acceptance, decoupled plan-only | ~40 | ~900 | Facade + ausgewählte `runner_*` | **MEDIUM** — viele Runner-Imports |
| `routes_governance.py` | Audit, sandbox, install, handoff, next-phase | ~16 | ~400 | `runner_*` governance | **MEDIUM** |
| `routes_runtime.py` | Core deploy plan/session/execute/write/cache | ~26 | ~650 | `deploy.*` core modules | **CRITICAL** |
| `routes_rescue.py` | Rescue-Orchestrierung (ohne Build/USB) | ~84 | ~2100 | `rescue.*`, `runner_rescue_*` | **HIGH** |
| `routes_rescue.py` (Build-Subrouter) oder `routes_rescue_build.py` | debian-live, ISO, chroot templates | ~21 | ~500 | `runner_rescue_*` build | **HIGH** |
| `routes_backup.py` | `/rescue/offline-backup-*`, backup-discovery | 2+ | ~100 | `rescue.backup_*`, runners | **HIGH** |
| `routes_restore.py` | restore-preview | 2+ | ~100 | `rescue.restore_*`, runners | **HIGH** |
| `routes_packaging.py` | Paket-/Release-Runner (falls ausgelagert) | ~2 | ~50 | `runner_*` packaging | **MEDIUM** |
| `routes_notifications.py` | (Reserve, aktuell 0 dedizierte Routen) | 0 | 0 | — | — |
| `routes_diagnostics.py` | Hardware-Test-Pläne, privileged validation | ~7 | ~180 | `runner_*` test-plan | **MEDIUM** |

### Orchestrator `routes.py` (Zielbild)

Nach D.5 bleibt ein dünner `routes.py`:

```python
router = APIRouter(prefix="/api/deploy", tags=["deploy"])
router.include_router(registry_router)
router.include_router(risk_gate_router)
# … weitere Subrouter
```

**Keine URL-Änderung** — nur interne Modulstruktur.

## Extraktionsreihenfolge (D.2–D.5)

| Phase | Slice | Begründung |
|-------|-------|------------|
| **D.2** | `routes_registry.py` | 0 Runner-Imports, reine Facade, GET-only — **erledigt** |
| **D.3** | `routes_risk_gate.py` | 0 Runner-Imports, Risk Gate bereits isoliert — **erledigt** |
| **D.4** | `routes_evidence.py` (Teilmenge) | Plan-only / decoupled zuerst; Execute-Routen ausgeschlossen |
| **D.5** | `routes_governance.py` | Audit/Sandbox ohne device-write |
| **D.6+** | runtime, rescue, backup, restore | **zuletzt** — CRITICAL/HIGH |

## Warum Registry und Risk Gate zuerst?

- Bereits über `runner_api_facade` implementiert (C.3/C.4)
- Keine direkten `runner_*`-Imports in diesen Handlern
- Extraktion = reines `include_router` ohne Verhaltensänderung

## Warum Execute-Routen zuletzt?

`/execute`, `/write/execute`, `real-write`, Rescue-USB/ISO — CRITICAL/HIGH. Erfordern Operator-Gates, E2E-Tests und ggf. separates Execute-Gate (nach C.7+).

## Nächste Phasen

- **D.2** Registry Router Extraction — **erledigt**
- **D.3** Risk Gate Router Extraction — **erledigt**
- **D.4** Evidence Router Extraction — **erledigt**
- **D.5** Governance Router — **nächster Schritt**
- **D.4** Evidence Router Extraction
- **D.5** Governance Router Extraction
