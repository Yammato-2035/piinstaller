# App-Decomposition — Boundary Report

**Stand:** 2026-06-02  
**Skript:** `scripts/check-module-boundaries.sh` (JSON, Exit 0)

## Ergebnis

| Feld | Wert |
|------|------|
| **status** | `review_required` |
| line_count | 17686 |
| include_router_count | 17 |
| warnings | `token_in_app:mkfs`, `token_in_app: dd `, `app_line_count_high:17686` |

## Interpretation

- **review_required** ist erwartbar: `app.py` enthält noch Legacy-Strings und viele Kern-Routen.
- Optionale Router und Middleware sind aus `app.py` entfernt; keine neuen verbotenen Rescue-Parser in `rescue_agent/`.
- Tieferer Legacy-Scan (lsblk/findmnt-Duplikate) liegt in unerreichbarem Tail des Skripts — JSON-Modus endet mit `exit 0`; Deep-Scan optional separat.

## Nächste Schritte

1. Routenweise `register_core_routes()` füllen.
2. Verbotene Tokens aus `app.py`-Strings in Services verschieben (nur wenn fachlich sicher).
3. Nach Operator-Deploy: Runtime `/api/version` mit `router_registry_summary` prüfen.
