# Deploy Rescue Domain Audit — D.13

**routes.py Zeilen:** 4057 (nach Slice)  
**Rescue-Routen gesamt:** 109  
**Extrahiert:** 4 → `routes_rescue_readonly.py`

## Klassifikation

| Klasse | Anzahl |
|--------|--------|
| execute | 2 |
| operator_required | 19 |
| plan_only | 88 |

## Extrahierte Routen (plan_only)

- `POST /rescue/live-os-base-decision` → routes_rescue_readonly.py
- `POST /rescue/component-inventory` → routes_rescue_readonly.py
- `POST /rescue/mvp-scope-gate` → routes_rescue_readonly.py
- `POST /rescue/debian-live-build-plan` → routes_rescue_readonly.py
