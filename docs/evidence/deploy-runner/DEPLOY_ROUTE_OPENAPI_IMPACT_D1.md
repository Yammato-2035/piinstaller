# Deploy Route OpenAPI Impact (Phase D.1)

**Keine OpenAPI-Änderung in D.1** — nur Impact-Analyse für D.2+.

## Unveränderte Endpunkte (Ziel)

Alle **237** Routen behalten:

- Pfad unter `/api/deploy/*` (bzw. Router-Prefix)
- HTTP-Methode
- Request/Response-Schema (Pydantic-Models bleiben vorerst in `routes.py` oder wandern 1:1 mit)

`include_router` ändert OpenAPI **nicht**, solange Prefix und Pfade identisch bleiben.

## Vorgeschlagene Swagger-Tags (D.2+)

| Tag | Routen | Quelle |
|-----|--------|--------|
| `deploy-runners-registry` | 5 GET | D.2 |
| `deploy-runners-risk-gate` | 5 GET | D.3 |
| `deploy-evidence` | ~40 POST | D.4 |
| `deploy-governance` | ~16 POST | D.5 |
| `deploy-runtime` | ~26 | D.6+ |
| `deploy-rescue` | ~84 | später |
| `deploy-rescue-build` | ~21 | später |
| `deploy-backup` | 2 | später |
| `deploy-restore` | 2 | später |

Aktuell: einheitlicher `deploy`-Tag (falls gesetzt) — keine Granularität.

## Swagger-Gruppen (Zielbild)

```
/api/deploy/
├── runners/          → registry + risk_gate (GET)
├── plan|session|execute/… → runtime
├── runner/manual-runtime/…  → evidence
├── rescue/…                 → rescue
├── rescue-stick/…           → rescue_build
└── version-*|legacy-*       → versioning
```

## DCC-Auswirkung

Development Control Center nutzt Deploy-Endpunkte selektiv. **LOW-Risk-Slices** (registry, risk_gate) sind für DCC read-only — keine UI-Änderung nötig.

Evidence/Governance-POSTs liefern Plan-Responses; DCC sollte `allowed_to_execute=false` aus Risk Gate respektieren (bereits C.4).

## Facade-decoupled Responses (C.5/C.6)

9 POST-Routen liefern zusätzliche Felder:

- `facade_decoupling_c5` / `facade_decoupling_c6`
- `risk_gate`
- `allowed_to_execute: false`

OpenAPI-Schema für diese Routen ist noch **Legacy-Runner-Shape + Facade-Envelope** — Dokumentation in späterer Phase, nicht D.1.

## Empfehlung D.2

Bei Registry-Extraktion: optional `tags=["deploy-runners-registry"]` am Subrouter — rein kosmetisch für Swagger, keine Breaking Change.
