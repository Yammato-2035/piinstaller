# Runtime Governance — Delegation Result

| Consumer | Delegation |
|----------|------------|
| `core/install_profile.get_install_profile_state` | `runtime_governance.service.materialize_install_profile_state` |
| `path_allowed_for_active_profile` | `decide_route_exposure` |
| `should_register_*` | `route_exposure` + bundle |
| `devserver/config.load_dev_server_config` | `build_devserver_policy` |
| `app.get_version` | `build_runtime_snapshot_parts` |

**`app.py`:** keine neue Fachlogik; Version-Endpoint nutzt Snapshot-Parts (-6 Zeilen Netto in Governance-Block).

**Legacy:** Routen, Response-Felder, `InstallProfileState`, `profile_gate_audit_route_paths` unverändert.

**Status:** `delegated`
