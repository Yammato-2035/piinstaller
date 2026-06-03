# KB — Ports und Profile (SetupHelfer)

Kurzfassung; Details: [docs/dev-dashboard/PORTS_AND_PROFILES.md](../../dev-dashboard/PORTS_AND_PROFILES.md)

- **API:** `127.0.0.1:8000`
- **UI/DCC:** `127.0.0.1:3001/?window=cockpit`
- **8080:** nginx, nicht DCC
- **QEMU:** Host-Proxy `8001`, Gast `http://10.0.2.2:8001`
- **Registry:** `config/runtime_ports.json`, auch in `/api/version` unter release

**release:** Dev-Routen blockiert (`PROFILE_ROUTE_BLOCKED`), `/api/version` bleibt 200.  
**local_lab:** Dev-Routen 200.

**Connection refused auf :8000** = Backend nicht erreichbar, nicht Profilblock.
