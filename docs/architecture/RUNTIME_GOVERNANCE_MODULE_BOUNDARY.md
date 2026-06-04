# Runtime Governance — Module Boundary

## Package

`backend/runtime_governance/`

| Modul | Verantwortung |
|-------|----------------|
| `models.py` | `RuntimeProfile`, `RuntimeCapabilities`, `DevServerPolicy`, `RouteExposureDecision`, `RuntimeSnapshotParts` |
| `profile_policy.py` | Profil-Auflösung, Capability-Matrix, Env-Overrides |
| `dev_control_policy.py` | DCC-Capability |
| `devserver_policy.py` | Dev-Server-Env-Defaults pro Profil |
| `route_exposure.py` | HTTP-Pfad-Gate, Router-Register-Hilfen |
| `runtime_snapshot.py` | `/api/version`-Fragmente (Profil, Gate, Ports) |
| `service.py` | `resolve_runtime_governance_bundle()`, `materialize_install_profile_state()` |

## Öffentliche API

```python
bundle = resolve_runtime_governance_bundle()
state = materialize_install_profile_state()  # legacy InstallProfileState
policy = build_devserver_policy(bundle.profile, bundle.capabilities)
decision = decide_route_exposure(path, bundle.capabilities)
parts = build_runtime_snapshot_parts(bundle, route_paths)
```

## Importgrenzen

* **Erlaubt:** `core.install_profile` (Dataclass + Audit-Helfer), `core.runtime_ports`
* **Verboten:** `app`, FastAPI, Backup/Restore/Rescue-Runner, subprocess/systemd

## Sicherheit

* `release`: Dev-Routen → `PROFILE_ROUTE_BLOCKED`
* `local_lab`: Lab-Capabilities; `require_token=false` nur wenn Env unset/leer
* Env-Overrides in `release`/`production` werden ignoriert (Warning)

## QEMU 143148 (separater Track)

Gast-Report scheitert an **Rescue-venv GLIBC**, nicht an Governance-Desync. Serial-SEND-Marker bestätigen Deploy/ISO-Fix-Pfad bis zum CLI-Start.
