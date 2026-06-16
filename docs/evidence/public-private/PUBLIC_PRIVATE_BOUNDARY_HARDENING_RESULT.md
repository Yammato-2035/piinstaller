# Public/Private Boundary Hardening Result

**Datum:** 2026-06-16  
**Skript:** `scripts/check-public-private-boundary.sh` (erweitert)

## Zusammenfassung

| Prüfung | Ergebnis |
|---------|----------|
| Verbotene Pfade im Tree | Keine gefunden |
| Geänderte Dateien (vor Commit) | Nur Doku/Scripts |
| Secret-Patterns | Keine Blocker |
| `.env` | Untracked — nicht stagen |

## Tabelle (Auszug)

| Datei/Pfad | Einstufung | Grund | Darf Public? | Maßnahme |
|------------|------------|-------|--------------|----------|
| `backend/cloud_backup/` | private_only | Kommerzielle Säule | Nein | Gate blockiert falls angelegt |
| `backend/telemetry_server/` | private_only | Interner Server | Nein | Gate Exit 11 |
| `backend/operator_dashboard/` | private_only | Cloud Operator UI | Nein | Gate Exit 14 |
| `backend/licensing/` | private_only | Billing/Lizenz | Nein | Gate Exit 12 |
| `docs/private-handoff/*` | public_safe | Handoff nur | Ja | Erlaubt |
| `docs/architecture/COMMERCIAL_MODULE_BOUNDARY.md` | public_safe | Grenzdoku | Ja | Term-Allowlist im Gate |
| `scripts/check-public-private-boundary.sh` | public_safe | Gate | Ja | Term-Allowlist |
| `.env` | blocked_from_public_git | Secrets-Risiko | Nein | Nie committen |
| `docs/api/msi_windows_precheck_contract.yaml` | public_safe_contract_only | Stub ohne Server | Ja | Keine Runtime |
| `linux-development-workstation` Blueprint | public_safe | Open-Core Profil | Ja | Doku only |

## Exit-Codes (neu dokumentiert)

| Code | Bedeutung |
|------|-----------|
| 0 | OK |
| 10 | private_code_detected |
| 11 | internal_telemetry_detected |
| 12 | commercial_logic_detected |
| 13 | secret_pattern_detected |
| 14 | operator_dashboard_detected |
| 17 | cloud_backup_detected |
| 18 | cloud_free_pro_detected |
| 19 | diagnostics_server_detected |
| 20 | review_required |

## Lauf nach Härtung

`./scripts/check-public-private-boundary.sh` → Exit **0** (erwartet nach Staging nur public-safe Dateien)
