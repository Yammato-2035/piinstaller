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

| Reihenfolge | Thema | Status | Abhängigkeit |
|-------------|-------|--------|----------------|
| — | DCC Live Acceptance (`local_lab`) | `blocked_by_operator_sudo` | Operator-Smoke vor weiterer Monolith-Arbeit |
| — | Runtime Governance Live Validation | `ready_for_operator_deploy_validation` | Deploy + release/local_lab-Parity |
| — | QEMU GLIBC / Rescue-venv Fix | `blocked` (`guest_rescue_venv_glibc_mismatch`) | Bookworm-kompatible Python-Laufzeit |
| 1 | API-Routen nach Domänen clustern (Dokumentation) | `deferred_until_live_validation` | `api_domain_mapping.json` |
| 2 | Evidence-/Report-Generierung entkoppeln | `deferred_until_live_validation` | DCC + Runtime-Governance live |
| 3 | Devserver-Agent / Guest-Report-Ingest Boundary | `deferred_until_live_validation` | QEMU GLIBC-Fix |
| 4 | Rescue-ISO-Pipeline von Kern-Backup trennen | mittel | nach Live-Validierung |
| 5 | UI ↔ API Contract stabilisieren | mittel | nach Live-Validierung |
| 6 | Storage-Erkennung zentralisieren | mittel-hoch | nach Live-Validierung |

*Nächster Monolith-Bereich erst nach DCC/Runtime-Governance-Liveprüfung und GLIBC-Track.*

## Explizit später

- Modulshop, Cloudserver Edition, Plesk (schwarz).
