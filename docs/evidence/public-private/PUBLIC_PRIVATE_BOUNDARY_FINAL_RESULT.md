# Public/Private Boundary — Abschlussbericht

**Datum:** 2026-06-16  
**Branch:** `main`  
**HEAD vorher:** `86ee180`  
**HEAD nachher:** uncommitted (dieser Auftrag)  
**Remote:** `https://github.com/Yammato-2035/piinstaller.git`  
**Sichtbarkeit:** **PUBLIC**

## 1. Arbeitsmodus

`public_safe_docs_and_contracts_only` — kein privater Produktcode erstellt.

## 2. Gate-Ergebnisse

| Gate | Ergebnis |
|------|----------|
| Runtime-Deploy-Gate | Exit 20 (Legacy, dev-dashboard 404 im release-Profil) |
| Backend-Version-Gate | Exit 0 |
| Module-Boundaries | review_required |
| Public-Private-Boundary | Exit 0 |
| Private-Import-Boundaries | Exit 20 (review_required) |

## 3. Public-safe Dateien (neu/aktualisiert)

- `scripts/check-public-private-boundary.sh`
- `scripts/check-private-import-boundaries.sh`
- `backend/core/redaction_contract.py`
- `backend/core/telemetry_client_contract.py`
- `backend/core/diagnostic_finding_contract.py`
- `backend/core/audit_event_contract.py`
- `backend/tests/test_redaction_contract_v1.py`
- `backend/tests/test_telemetry_client_contract_v1.py`
- `backend/tests/test_public_private_boundaries_v1.py`
- `docs/architecture/*` (Public/Private-Strategie, Modulgrenzen)
- `docs/private-handoff/*` (5 Handoff-Dokumente)
- `docs/runbooks/PRIVATE_REPOSITORY_SETUP_RUNBOOK_{DE,EN}.md`
- `docs/legal/*` (8 Checklisten)
- `docs/api/*_openapi.yaml` (3 Contracts)
- `docs/evidence/public-private/*`, `docs/evidence/monolith/*`
- FAQ/KB/Roadmap/Changelog-Updates

## 4. Private-only (bewusst NICHT gebaut)

- Cloudserver Edition Implementierung
- Interner Telemetrie-Server (Ingest/Store/Operator-API)
- Diagnostikserver mit internen Regeln
- Operator-Dashboard UI
- Lizenz-/Billing-/Abo-Logik
- Kostenlose Plesk-Version

## 5. Monolithen (Top-Kandidaten)

| Datei | Zeilen | Risiko |
|-------|-------:|--------|
| `backend/app.py` | 15142 | CRITICAL |
| `frontend/src/pages/BackupRestore.tsx` | 3992 | HIGH |
| `backend/deploy/routes.py` | 3704 | HIGH |
| `backend/tools/backup_runner.py` | 1583 | HIGH |
| `backend/core/dev_dashboard.py` | 1217 | MEDIUM |

Details: `docs/evidence/monolith/MONOLITH_CANDIDATES.md`

## 6. Core-Facades

| Facade | Status |
|--------|--------|
| `storage_facade.py` | vorhanden, wiederverwendet |
| `mount_facade.py` | vorhanden, wiederverwendet |
| `safety_facade.py` | vorhanden, wiederverwendet |
| `redaction_contract.py` | neu (public-safe) |
| `telemetry_client_contract.py` | neu (public-safe) |
| `diagnostic_finding_contract.py` | neu (public-safe) |
| `audit_event_contract.py` | neu (public-safe) |

## 7. Tests

| Test | Ergebnis |
|------|----------|
| `test_redaction_contract_v1.py` | 4 passed |
| `test_telemetry_client_contract_v1.py` | 4 passed |
| `test_public_private_boundaries_v1.py` | 6 passed |
| `test_core_safety_facade_v1.py` | passed |
| `test_core_storage_facade_v1.py` | 2 pre-existing failures (mock `detect_block_devices` — nicht durch diesen Auftrag verursacht) |
| `test_module_boundaries_v1.py` | passed |
| Boundary-Skripte | PP Exit 0, PI Exit 20 |

## 8. Versionierung

**Empfehlung:** `version_change_required` → **1.8.0.0** (neuer Bereich: Public/Private-Architekturgrenze)  
**Nicht automatisch angewendet** — nur Dokumentation/Contracts in diesem Lauf; Version-Bump beim Commit durch Operator.

## 9. Commit/Push

- **Commit-Status:** nicht committed (kein `git add -A`)
- **Push-Status:** nicht gepusht

## 10. Explizite Nicht-Aktionen

- Kein produktiver Deploy
- Kein Plesk-Live-Change
- Keine Cloudserver-/Telemetrie-/Diagnostikserver-Implementierung in Public GitHub
- Keine kostenlose Plesk-Version gebaut
- Keine echten Telemetriedaten gesendet
- Keine Safety-Gates geschwächt
- Keine Secrets committed

## 11. Nächster empfohlener Schritt

**A.** Separater Prompt: Monolith-Facade-Migration Set 2 (Rescue → Core-Facades)  
oder **B.** Privates Repository-Scaffold außerhalb Public GitHub  
oder **C.** Telemetrie-Client-Contract im Rettungsstick
