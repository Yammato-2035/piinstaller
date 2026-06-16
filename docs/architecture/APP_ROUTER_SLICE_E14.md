# App Router Slice E.14

**Phase:** Monolith-Auflösung — Security API  
**Version:** 1.8.12.0

## Scope

| Route | Handler |
|-------|---------|
| `POST /api/security/scan` | `security_scan` |
| `GET /api/security/status` | `security_status` |
| `POST /api/security/firewall/enable` | `enable_firewall` |
| `POST /api/security/firewall/install` | `install_firewall` |
| `GET /api/security/firewall/rules` | `get_firewall_rules` |
| `POST /api/security/firewall/rules/add` | `add_firewall_rule` |
| `DELETE /api/security/firewall/rules/{rule_number}` | `delete_firewall_rule` |
| `POST /api/security/configure` | `configure_security` |

Nach E.14 enthält `app.py` **keine** `@app.*("/api/security/…")` mehr.

## Security

- `configure` und `firewall/enable`: sudo_store nur mit `has_password()`-Guard
- Helfer (`_open_terminal_with_command`, `_run_apt_*`, `get_updates_categorized`) bleiben in `app.py`

## Tests

`test_app_router_slice_e14.py` — 8 Routen im Security-Router.
