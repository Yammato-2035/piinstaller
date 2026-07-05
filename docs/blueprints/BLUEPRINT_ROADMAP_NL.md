> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/blueprints/BLUEPRINT_ROADMAP_EN.md`). Bitte bei Release manuell gegenlesen.

# Blueprint roadmap

**Status:** 2026-06-16

## Priority

| Prio | Blueprint | Public/private | MSI |
|------|-----------|----------------|-----|
| 1 | `Linux-development-workstation` | public-safe | **Ja** (after Windows B/V/R) |
| 2 | `heimserver-basic` | public-safe (core) | Nee |
| 3 | `pihole-dns` | public-safe | Nee |
| 4 | `webserver-basic` | public-safe | Nee |
| 5 | `Volgendecloud-cloud` | private (`commercial-*`) | Nee |
| 6 | `mailserver-later` | private | Nee |

## Neet in public roadmap implementation

- Cloud edition free/pro code
- Telemetry / diagNeestics server
- Operator-managed blueprints

## MSI sequence

1. Commercial/public boundary (this run) ✅
2. MSI precheck (alleen-lezen, separate prompt)
3. MSI Terugup (operator)
4. MSI verify
5. MSI Herstel test
6. Wipe approval + Linux install
7. `Linux-development-workstation` + Linux B/V/R
