# Ports & Backend Release Restart — Phase 0

**Datum:** 2026-06-03  
**HEAD:** `23d2361` (vor Commit)

| Prüfpunkt | Wert |
|-----------|------|
| Branch | `main` |
| Backend-Service | **active** |
| Web-Service | **active** |
| Port 8000 listening | **yes** |
| Port 3001 listening | **yes** |
| Port 8080 listening | **yes** (nginx, **nicht DCC**) |
| `/api/version` HTTP 200 | **yes** |
| Aktuelles Profil | **release** |
| `dev_control_enabled` | **false** |
| DCC unter release blockiert | **expected** |
| **Klassifikation (Operator-Meldung)** | `backend_down` / `restart_race` (transient nach Release-Restore) |
| **Klassifikation (jetzt)** | `release_profile_expected_dcc_block` + **recovered** |
