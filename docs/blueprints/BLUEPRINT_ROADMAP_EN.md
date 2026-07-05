# Blueprint roadmap

**Status:** 2026-06-16

## Priority

| Prio | Blueprint | Public/private | MSI |
|------|-----------|----------------|-----|
| 1 | `linux-development-workstation` | public-safe | **Yes** (after Windows B/V/R) |
| 2 | `heimserver-basic` | public-safe (core) | No |
| 3 | `pihole-dns` | public-safe | No |
| 4 | `webserver-basic` | public-safe | No |
| 5 | `nextcloud-cloud` | private (`commercial-*`) | No |
| 6 | `mailserver-later` | private | No |

## Not in public roadmap implementation

- Cloud edition free/pro code
- Telemetry / diagnostics server
- Operator-managed blueprints

## MSI sequence

1. Commercial/public boundary (this run) ✅
2. MSI precheck (read-only, separate prompt)
3. MSI backup (operator)
4. MSI verify
5. MSI restore test
6. Wipe approval + Linux install
7. `linux-development-workstation` + Linux B/V/R
