# Rescue-Agent Report-Ingest — Stub-Smoke Ergebnis

**Stand:** 2026-06-02  
**Status:** **ok**

## Operator-Smoke

| Feld | Wert |
|------|------|
| Smoke-Dir | `rescue_agent_ingest_operator_smoke_20260602_182452` |
| Skript | `rescue-agent-ingest-stub-smoke-operator.sh` |
| Ingest-Doku | `RESCUE_AGENT_OPERATOR_SMOKE_INGEST.md` |

## Ergebnis

| Phase | Status |
|-------|--------|
| Release-Block vorher | **ok** |
| `local_lab` + Profil-Guard | **ok** |
| Negative Tests | **403** `RESCUE_AGENT_INVALID_SESSION` |
| Registration | **200** `RESCUE_AGENT_REGISTER_OK`, `pending` |
| Valid Report | **200** `RESCUE_AGENT_REPORT_ACCEPTED` + E2EE-Envelope |
| Release nach Trap | **ok** — `PROFILE_ROUTE_BLOCKED` wieder aktiv |

## Contract

- E2EE: **contract_stub_only** (Envelope `1.0`, `X25519-Ed25519-AEAD`)
- nftables: **preview_only_apply_false**
- Kein Write/Apply; Stub/Contract, kein Produktiv-Agent

## Historie

Frühere Blocker (`PROFILE_ROUTE_BLOCKED` in release, sudo) — durch guarded Operator-Script behoben.

JSON: `rescue_agent_report_ingest_stub_smoke_latest.json`
