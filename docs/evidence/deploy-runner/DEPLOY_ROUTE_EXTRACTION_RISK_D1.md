# Deploy Route Extraction Risk (Phase D.1)

Bewertung pro Domain für physische Router-Extraktion (D.2+). **D.1 führt keine Extraktion durch.**

## Risk-Matrix

| Domain | Routen | API | OpenAPI | Tests | Runtime | DCC | Gesamt |
|--------|--------|-----|---------|-------|---------|-----|--------|
| registry | 5 | LOW | LOW | LOW | LOW | LOW | **LOW** |
| risk_gate | 5 | LOW | LOW | LOW | LOW | LOW | **LOW** |
| evidence | 40 | LOW | LOW | MEDIUM | LOW | MEDIUM | **LOW–MEDIUM** |
| governance | 16 | MEDIUM | LOW | MEDIUM | LOW | MEDIUM | **MEDIUM** |
| diagnostics | 7 | MEDIUM | LOW | MEDIUM | MEDIUM | LOW | **MEDIUM** |
| versioning | 23 | MEDIUM | MEDIUM | MEDIUM | MEDIUM | MEDIUM | **MEDIUM–HIGH** |
| packaging | 0* | — | — | — | — | — | — |
| rescue_build | 21 | HIGH | MEDIUM | HIGH | HIGH | HIGH | **HIGH** |
| rescue | 84 | HIGH | HIGH | HIGH | HIGH | HIGH | **HIGH** |
| backup | 2 | HIGH | MEDIUM | HIGH | HIGH | MEDIUM | **HIGH** |
| restore | 2 | HIGH | MEDIUM | HIGH | HIGH | MEDIUM | **HIGH** |
| runtime | 26 | CRITICAL | HIGH | HIGH | CRITICAL | HIGH | **CRITICAL** |
| notifications | 0 | — | — | — | — | — | — |
| telemetry | 0 | — | — | — | — | — | — |
| development_server | 0 | — | — | — | — | — | — |
| development_control_center | 0 | — | — | — | — | — | — |
| unknown | 6 | MEDIUM | LOW | MEDIUM | LOW | LOW | **MEDIUM** |

\*packaging: keine eigenständigen Pfad-Routen; Runner-Kategorie existiert in Registry.

## Erste Extraktionskandidaten (3 sicherste Slices)

| Kandidat | Domain | Routen | Risiko | Empfehlung |
|----------|--------|--------|--------|------------|
| **D.2** | registry | 5 | LOW | **Zuerst** — `include_router`, nur `runner_api_facade`, GET-only |
| **D.3** | risk_gate | 5 | LOW | **Zweitens** — gleiche Facade-Schicht, keine Runner-Imports |
| **D.4** | evidence (Teilmenge) | 9 decoupled + plan-only subset | LOW–MEDIUM | **Drittens** — C.5/C.6 decoupled + weitere `allowed_plan_only` |

### Begründung

1. **Registry:** Handler sind 1-Zeilen-Facade-Delegation (`build_runner_catalog`, `get_runner_registry_entry`). Kein `from deploy.runner_*` in diesen Funktionen. OpenAPI-Pfade unverändert.

2. **Risk Gate:** Analog — `build_runner_risk_gate_summary`, `list_runner_plan_allowed`, etc. C.4-Garantie `allowed_to_execute=false` bleibt in Facade.

3. **Evidence:** 9 Routen bereits decoupled (`build_plan_only_response`). Weitere Evidence-Routen sind überwiegend `evidence_write` / `lab_only` — extrahierbar nach Registry/Risk-Gate-Muster, aber mit mehr Runner-Imports als D.2/D.3.

### Bewusst ausgeschlossen von frühen Slices

| Domain | Grund |
|--------|-------|
| runtime | `/execute`, `/write/execute` — CRITICAL |
| rescue / rescue_build | ISO/USB/Build — HIGH, Operator-Pfade |
| backup / restore | Datenpfade — HIGH |
| versioning (apply) | `*-apply`-Routen — system_change |

## Skala

| Stufe | Kriterium |
|-------|-----------|
| LOW | Read-only, Facade-only, keine Side-Effects |
| MEDIUM | Plan-only POST, evidence_write, Governance |
| HIGH | Rescue, Backup, Restore, Build |
| CRITICAL | Execute, device_write, real-write |
