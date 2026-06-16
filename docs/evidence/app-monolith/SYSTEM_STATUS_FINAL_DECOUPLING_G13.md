# System Status Final Decoupling — G.13

## Vorher

`system_status_facade` → `import app` in:
- `build_backend_runtime_section`
- `build_installation_section`
- `build_profile_section`

## Nachher

`system_runtime_info.py` (SYSTEM_RUNTIME_INFO_VERSION=1)
- `build_runtime_info`
- `build_installation_info`
- `build_profile_info`

Facade: nur Delegation, **kein import app**.
