# Monolith-Refactoring – Plan (nur Vorbereitung)

**Phase:** Planung – **keine** Dateiverschiebungen ohne Release-Gate.

## Prinzipien

1. Kleine Schritte, jeweils grüne CI + gezielte Teil-Tests.  
2. Zuerst Evidence und Domänenbeschreibung (`DOMAIN_BOUNDARIES.md`, `dangerous_couplings.json`).  
3. Backup/Restore/Safety zuletzt anfassen – höchstes Risiko.

## Erledigt (2026-06-04)

| Schritt | Thema | Modul |
|---------|-------|-------|
| 0 | **Runtime Governance** (Profil, dev_control, Devserver, Route-Gate, Version-Snapshot) | `backend/runtime_governance/` — Evidence `RUNTIME_GOVERNANCE_*`, Architektur `RUNTIME_GOVERNANCE_MODULE_BOUNDARY.md` |

## Geplante Reihenfolge (nach Audit)

| Reihenfolge | Thema | Abhängigkeit |
|-------------|-------|----------------|
| 1 | API-Routen nach Domänen clustern (Dokumentation) | `api_domain_mapping.json` |
| 2 | Evidence-/Report-Generierung entkoppeln | niedriges Risiko |
| 3 | Rescue-ISO-Pipeline von Kern-Backup trennen | mittel |
| 4 | UI ↔ API Contract stabilisieren | mittel |
| 5 | Storage-Erkennung zentralisieren | mittel-hoch |

*Diese Reihenfolge wird nach Abschluss von Prompt 5 konkretisiert.*

## Explizit später

- Modulshop, Cloudserver Edition, Plesk (schwarz).
