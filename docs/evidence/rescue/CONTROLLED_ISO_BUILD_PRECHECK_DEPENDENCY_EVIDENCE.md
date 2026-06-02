# Controlled ISO Build Precheck — Dependency Evidence

**Stand:** 2026-06-02

## Voraussetzungen

| Kriterium | Status |
|-----------|--------|
| Fleet-Smoke | **green** |
| DCC-Port-Mapping | **green** (3001 UI, 8000 API, 8080 nginx) |
| Rescue-Agent-Ingest | **ok** |
| `release_restored_after` | **true** |
| E2EE | **contract_stub_only** |
| nftables | **preview_only_apply_false** |

## Smoke-Dir-Mismatch (182452 vs 182622)

| Verzeichnis | Rolle |
|-------------|--------|
| `…_182452` | **Kanonical** — in Commit `4df53eb`, JSON, `RESCUE_AGENT_OPERATOR_SMOKE_INGEST.md` |
| `…_182622` | **Duplikat** — zweiter erfolgreicher Operator-Lauf (andere Session-IDs), gleiches Ergebnis |

Beide Logs enthalten `PROFILE_GUARD_OK`, `RESCUE_AGENT_REGISTER_OK`, `RESCUE_AGENT_REPORT_ACCEPTED`, Trap-Release.

**Bewertung:** **Doku-konsistent** — kein Evidence-Problem. `182622` ist optionaler Wiederholungslauf, nicht der referenzierte Kanon.

## Referenzen

- `FLEET_HEARTBEAT_FIX_AFTER_SCRIPT_FIX_RESULT.md`
- `DCC_READONLY_SMOKE_AFTER_PORT_MAPPING.md`
- `rescue_agent_report_ingest_stub_smoke_latest.json`
