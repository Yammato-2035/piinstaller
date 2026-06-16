# Blueprint Roadmap

**Stand:** 2026-06-16

## Priorität

| Prio | Blueprint | Public/Private | MSI |
|------|-----------|----------------|-----|
| 1 | `linux-development-workstation` | public-safe | **Ja** (nach Windows B/V/R) |
| 2 | `heimserver-basic` | public-safe (Core) | Nein |
| 3 | `pihole-dns` | public-safe | Nein |
| 4 | `webserver-basic` | public-safe | Nein |
| 5 | `nextcloud-cloud` | private (`commercial-*`) | Nein |
| 6 | `mailserver-later` | private | Nein |

## Nicht in Public Roadmap-Implementierung

- Cloud Edition Free/Pro Code
- Telemetrie-/Diagnostikserver
- Operator-managed Blueprints

## MSI-Sequenz

1. Commercial/Public Boundary (dieser Lauf) ✅
2. MSI Precheck (read-only, separater Prompt)
3. MSI Backup (Operator)
4. MSI Verify
5. MSI Restore-Test
6. Wipe-Freigabe + Linux-Install
7. `linux-development-workstation` + Linux B/V/R
