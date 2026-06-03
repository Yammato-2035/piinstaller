# Rescue Agent Contract Result — Rescue Stick Fleet Wave

**Datum:** 2026-06-03  
**HEAD:** `2ca3a70`  
**Branch:** `main`  
**Modus:** statisch (Runtime-Gate legacy informational unter `release`)

## Phase-0 Gate

| Check | Ergebnis |
|-------|----------|
| `check-runtime-deploy-gate.sh` | Exit 20 — `LEGACY_GATE_NON_PROFILE_AWARE` (dev-dashboard 404 unter release, erwartet) |
| Entscheidung | **`runtime_gate_blocked_static_analysis_only`** — keine Runtime-Smokes auf :8000 |
| `setuphelfer-backend.service` | active |
| `setuphelfer.service` | active |
| Public Repo | PUBLIC — **NDA risk:** keine Secrets/PII in Evidence |

## Heartbeat-Fix (Phase 1)

| Bereich | Status |
|---------|--------|
| Backend `heartbeat_fleet_session` | `status=running` → ignoriert, `agent_state=alive` |
| Shell `fleet_session_heartbeat_payload` | `running` → nur `agent_state`, kein invalid status |
| Tests | 6 unittest + Shell-Payload inkl. `running` — **OK** |
| Create → Heartbeat → Finish | unittest flow OK, kein Fake-Gast |

## Rescue Agent Module (Phasen 2–8)

| Modul | Status |
|-------|--------|
| Discovery | **implemented_stub** (`backend/rescue_agent/discovery.py`) |
| Pairing/Registration | **implemented_stub** |
| E2EE Envelope | **contract_stub** (kein Produktions-Krypto) |
| nftables Policy | **preview_only**, `apply_allowed=false` |
| System Report | **implemented_stub** (Core-Facades wenn vorhanden) |
| API Routes | **implemented_stub** (local_lab gating, release block) |
| Dashboard | **implemented_stub** (`RescueAgentPanel`) |
| Live Setup Menu | **stub** (`RescueLiveSetupMenu.tsx`) |
| Boot Menu Branding | **review_required** (SVG→PNG Dependency) |

## Tests (Phase 13)

| Suite | Ergebnis |
|-------|----------|
| Backend pytest (7 Dateien, 32 Tests) | **32 passed** |
| Fleet/rescue shell payloads | **OK** |
| Frontend Vitest | **54 passed** |
| Frontend typecheck | **frontend_typecheck_missing_script** |

## Nicht ausgeführt

Kein ISO-Build · Kein lb build · Kein QEMU · Kein USB/dd · Kein Backup · Kein Restore · Kein apt · Kein Deploy · Kein Push

## Nächster Schritt (nur Vorschlag)

1. `local_lab` Live-Smoke: Create → Heartbeat → Finish → Rescue Session im DCC  
2. Rescue-Agent-Report-Ingest live testen  
3. `devserver_agent` ISO-Packaging fix (siehe `QEMU_GUEST_AGENT_AFTER_REGISTRY_NEXT_PROMPT.md`)  
4. Kontrollierter ISO-Build  
5. USB-Write nur mit Operator-Doppelbestätigung
