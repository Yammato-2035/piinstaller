# Monolith-Decomposition-Plan (app.py)

## Phase A (erledigt in Lauf 2026-06-02)

1. Bootstrap-Schicht (`app_bootstrap`)
2. Middleware-Registry
3. Optionale Router-Registry + Startup-Diagnostik
4. Dev-Dashboard-Status-Service-Adapter
5. Safety-Facade ergänzt; Storage/Mount-Facades unverändert nutzbar

## Phase B (folgt)

1. `register_core_routes()` — routenweise APIRouter aus `app.py` extrahieren
2. Domain-Module: backup, restore, partitions, deploy (je ein Router + Service)
3. Boundary-Guard verschärfen (`review_required` → `ok`)

## Regeln

- Keine API-Brüche ohne Versionierung
- Keine parallelen lsblk/findmnt-Parser in Rescue-Code
- ISO/Deploy nur nach Gate + Operator-Freigabe
