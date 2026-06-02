# Rescue-Agent Report-Ingest — Stub-Smoke Ergebnis

**Stand:** 2026-06-02  
**Status:** **blocked** (`rescue_agent_ingest_blocked_sudo_required`)

## Zusammenfassung

| Phase | Ergebnis |
|-------|----------|
| 0–1 Release-Baseline | **ok** — `PROFILE_ROUTE_BLOCKED` auf allen Rescue-Agent-Routen |
| 2 `local_lab` aktivieren | **blocked** (Agent: sudo Passwort; Operator-Terminal: Profil-Toggle ohne curl-Tests) |
| 3–7 Live-Ingest | **not_run** |
| 8 Release nach Smoke | Runtime bereits **`release`** (Operator-Toggle zurück) |

**Smoke-Dir (Workspace, nicht committed):** `docs/evidence/rescue/rescue_agent_ingest_operator_smoke_20260602_181543/`  
**Rohlog:** `smoke.log` — Baseline + sudo-Block

## Release-Baseline (belegt)

| Feld | Wert |
|------|------|
| `install_profile` | `release` |
| `rescue_agent_router_status` | `disabled_by_profile` |
| `GET /api/rescue-agent/sessions` | 404 `PROFILE_ROUTE_BLOCKED` |

## Operator-Hinweis

Terminal-6 zeigt `local_lab` → `release` Toggle (exit 0), aber **keine** Register/Report-curls. Vollständigen Smoke in interaktivem Terminal mit sudo ausführen (siehe Runbook unten).

## Contract (unverändert)

| Thema | Status |
|-------|--------|
| E2EE | `contract_stub_only` |
| nftables | `preview_only_apply_false` |
| Write/Apply unter `/api/rescue-agent` | **none** |
| Live-API-Body | `session_id`, `agent_id`, `test_mode_allow_unencrypted` |

Unit-Referenz: `backend/tests/test_rescue_agent_api_contract_v1.py` (pytest im Smoke-Dir `raw/pytest_contract_reference.log` — **nicht** Live-Smoke).

## Operator-Runbook (vollständiger Smoke)

```bash
cd /home/volker/piinstaller
TS="$(date -u +%Y%m%d_%H%M%S)"
SMOKE_DIR="docs/evidence/rescue/rescue_agent_ingest_operator_smoke_${TS}"
RAW_DIR="$SMOKE_DIR/raw"
mkdir -p "$RAW_DIR"
LOG="$SMOKE_DIR/smoke.log"
# … Phasen 1–8 wie STRICT-MODE-Auftrag …
```

Nach erfolgreichem Lauf: `rescue_agent_report_ingest_stub_smoke_latest.json` auf `ok` setzen.

## JSON

`rescue_agent_report_ingest_stub_smoke_latest.json`

## Bewertung

**Kein Fake-Green.** Live-Ingest unbelegt bis Operator-Smoke mit Rohlogs abgeschlossen.
