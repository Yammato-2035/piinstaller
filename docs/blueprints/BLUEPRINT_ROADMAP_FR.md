> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/blueprints/BLUEPRINT_ROADMAP_EN.md`). Bitte bei Release manuell gegenlesen.

# Blueprint roadmap

**Status:** 2026-06-16

## Priority

| Prio | Blueprint | Public/private | MSI |
|------|-----------|----------------|-----|
| 1 | `Linux-development-workstation` | public-safe | **Oui** (after Windows B/V/R) |
| 2 | `heimserver-basic` | public-safe (core) | Non |
| 3 | `pihole-dns` | public-safe | Non |
| 4 | `webserver-basic` | public-safe | Non |
| 5 | `Suivantcloud-cloud` | private (`commercial-*`) | Non |
| 6 | `mailserver-later` | private | Non |

## Nont in public roadmap implementation

- Cloud edition free/pro code
- Telemetry / diagNonstics server
- Operator-managed blueprints

## MSI sequence

1. Commercial/public boundary (this run) ✅
2. MSI precheck (lecture seule, separate prompt)
3. MSI Retourup (operator)
4. MSI verify
5. MSI Restauration test
6. Wipe approval + Linux install
7. `Linux-development-workstation` + Linux B/V/R
