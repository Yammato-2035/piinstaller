# Deploy Route Ownership Matrix (Phase D.6)

| Domain | Owner-Modul | Routen | Status | Nächste Aktion |
|--------|-------------|-------:|--------|----------------|
| registry | `routes_registry.py` | 5 | **extracted** | — |
| risk_gate | `routes_risk_gate.py` | 5 | **extracted** | — |
| evidence | `routes_evidence.py` + `routes.py` | 6 + ~32 | **partial** | D.7 plan-only |
| governance | `routes_governance.py` + `routes.py` | 3 + ~31 | **partial** | D.7+ audit/sandbox |
| versioning | `routes.py` | ~16 | **routes_py** | D.10 |
| runtime | `routes.py` | ~13 | **routes_py** | D.11 read-only first |
| rescue | `routes.py` | ~91 | **routes_py** | D.13+ plan-only |
| rescue_build | `routes.py` | ~18 | **routes_py** | D.13 plan-only |
| rescue_usb | `routes.py` | 0* | **routes_py** | D.14 |
| backup | `routes.py` | ~2 | **routes_py** | unsafe_to_extract_now |
| restore | `routes.py` | ~2 | **routes_py** | unsafe_to_extract_now |
| diagnostics | `routes.py` | ~7 | **routes_py** | D.8 |
| packaging | `routes.py` | ~2 | **partial** | D.12 |
| notifications | — | 0 | **blocked** | keine Routen |
| unknown | `routes.py` | ~17 | **routes_py** | D.6 Klassifikation |

\*rescue_usb-Pfade unter rescue/rescue_build klassifiziert.

## Status-Legende

- **extracted** — vollständig in Subrouter (Facade-only)
- **partial** — Teilmenge extrahiert
- **routes_py** — verbleibt im Monolith
- **blocked** — noch keine dedizierten Routen
- **unsafe_to_extract_now** — Execute/Write/Backup/Restore — Execute-Gate erforderlich
