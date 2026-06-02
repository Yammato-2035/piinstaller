# Rescue-Agent Report-Ingest — Stub-Smoke Ergebnis

**Stand:** 2026-06-02  
**Status:** **blocked** (`profile_guard_violation_and_sudo_required`)

## Root Cause (Operator-Terminal 6)

Register/Report-curls liefen **nach** `release`-Restore, **ohne** vorher `install_profile=local_lab` zu verifizieren:

```json
{"status":"error","code":"PROFILE_ROUTE_BLOCKED","path":"/api/rescue-agent/register"}
{"status":"error","code":"PROFILE_ROUTE_BLOCKED","path":"/api/rescue-agent/system-report"}
```

Das ist **kein API-Fehler**, sondern **Profil-Gate korrekt**. Vor jedem Live-Test: `curl …/api/version | jq .install_profile` → muss `local_lab` sein.

## Durchgeführt

| Phase | Ergebnis |
|-------|----------|
| Release-Baseline | **ok** — Rescue-Routen `PROFILE_ROUTE_BLOCKED` |
| Operator Register/Report (Terminal 6) | **blocked** — lief unter **`release`** |
| Guarded Script (Agent) | **blocked** — sudo Passwort |
| Live-Ingest unter `local_lab` | **not_run** |

## Operator — Guarded Script (Release-Trap)

Im **interaktiven Terminal 6** ausführen:

```bash
cd /home/volker/piinstaller
./scripts/rescue-live/rescue-agent-ingest-stub-smoke-operator.sh
```

Das Skript:

1. Belegt Release-Baseline  
2. Aktiviert `local_lab` + **PROFILE_GUARD** (`exit 11/12` wenn nicht `local_lab`)  
3. Negative → Register → Valid Report (nur unter `local_lab`)  
4. **`trap restore_release EXIT`** — stellt `release` wieder her  

Nach Erfolg: JSON `release_restored_after=true`, Status `ok` wenn Register+Report HTTP 200.

## Contract

| Thema | Status |
|-------|--------|
| E2EE | `contract_stub_only` |
| nftables | `preview_only_apply_false` |
| API-Body | `session_id`, `agent_id`, `test_mode_allow_unencrypted` |

## Smoke-Dirs (Workspace)

| Verzeichnis | Inhalt |
|-------------|--------|
| `…_181543` | Agent-Baseline, sudo block |
| `…_182142` | Guarded Script Baseline, sudo block |

## Bewertung

**Kein Fake-Green.** ISO-Precheck bleibt blockiert bis guarded Smoke `ok`.

JSON: `rescue_agent_report_ingest_stub_smoke_latest.json`
