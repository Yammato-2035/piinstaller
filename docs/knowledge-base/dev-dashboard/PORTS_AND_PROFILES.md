# KB — Ports und Profile (SetupHelfer)

Kurzfassung; Details: [docs/dev-dashboard/PORTS_AND_PROFILES.md](../../dev-dashboard/PORTS_AND_PROFILES.md)

- **API:** `127.0.0.1:8000`
- **UI/DCC:** `127.0.0.1:3001/?window=cockpit`
- **8080:** nginx, nicht DCC
- **QEMU:** Host-Proxy `8001`, Gast `http://10.0.2.2:8001`
- **Registry:** `config/runtime_ports.json`, auch in `/api/version` unter release (live verifiziert 2026-06-03, Evidence `RUNTIME_PORTS_REGISTRY_DEPLOY_INGEST_RESULT.md`)

**release:** Dev-Routen blockiert (`PROFILE_ROUTE_BLOCKED`), `/api/version` bleibt 200.  
DCC ist unter `release` bewusst gesperrt (disabled page als erwartbarer Sicherheitszustand; kein Funktionsnachweis).
**local_lab:** Dev-Routen 200 und DCC live-funktional erst nach Smoke/HTTP 200 unter `local_lab` gültig.

**Canonical policy source (2026-06-04):** `backend/runtime_governance/` — `install_profile.py` und `devserver/config.py` delegieren dorthin.

**Connection refused auf :8000** = Backend nicht erreichbar, nicht Profilblock.
