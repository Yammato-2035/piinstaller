# Runtime Governance — Boundary Audit

## Ist-Zustand (vor Extraktion)

| Bereich | Ort |
|---------|-----|
| Profil-Auflösung + Capability-Matrix | `backend/core/install_profile.py` |
| HTTP-Route-Gate | Middleware in `app.py` + `path_allowed_for_active_profile` |
| Devserver-Profil-Sync | `backend/devserver/config.py` (`_profile_dev_server_defaults`) |
| `/api/version` Snapshot | `app.py` `get_version()` (~60 Zeilen) |
| Runtime Ports | `backend/core/runtime_ports.py` + Registry JSON |
| Router-Registrierung | `app_bootstrap/router_registry.py` + `should_register_*` in install_profile |
| Startup-Diagnostik | `app_bootstrap/startup_diagnostics.py` |

## Duplikate / Streuung

* Profil → Devserver-Defaults separat in `devserver/config.py` (Desync-Risiko wie Run 212528).
* `get_install_profile_state()` mehrfach pro Request (Middleware + Config).
* `app.py` **17741** Zeilen — Runtime-Felder in Version-Endpoint inline zusammengebaut.

## Nach Extraktion

**Kanonische Schicht:** `backend/runtime_governance/`

* `profile_policy.py` — Profil + Capabilities
* `devserver_policy.py` — Devserver-Env-Defaults
* `route_exposure.py` — Route-Gate
* `runtime_snapshot.py` — `/api/version`-Fragmente
* `service.py` — Bundle + `materialize_install_profile_state()`

`install_profile.py` → dünne Delegation (Legacy-API erhalten).  
`devserver/config.py` → nutzt `build_devserver_policy`.  
`app.py` `get_version` → `build_runtime_snapshot_parts`.

## Nicht verschoben

Backup/Restore/USB/Rescue-Runner, FastAPI-Router-Definitionen, Deploy, systemd.

## Nicht gelöst durch Refaktor

* sudo/Operator-Grenzen
* stale Build-Artefakte / ISO-Rebuild
* QEMU-Gast **GLIBC/venv** (Run 143148)
* Externe USB-Hardware

## Kreisabhängigkeiten

`runtime_governance` importiert **nicht** `app.py`.  
Erlaubt: `core.install_profile.InstallProfileState` (Typ), `core.runtime_ports`, `profile_gate_audit_route_paths` (Legacy-Audit-Parität).
