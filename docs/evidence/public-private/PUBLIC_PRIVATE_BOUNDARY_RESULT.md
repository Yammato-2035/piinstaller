# Public/Private Boundary Gate — Ergebnis

**Stand:** 2026-06-16  
**Gate:** `scripts/check-public-private-boundary.sh` (Exit 0)  
**Import-Gate:** `scripts/check-private-import-boundaries.sh` (Exit 20, review_required)

## Zusammenfassung

| Prüfung | Status |
|---------|--------|
| Verbotene private Pfade im Tree | OK — keine `cloudserver_private`, `telemetry_server`, `operator_dashboard` |
| Verbotene Begriffe in geänderten Dateien | OK |
| Secret-Pattern in geänderten Dateien | OK |
| Interne Domains | OK |
| Docker Compose DB/Redis öffentlich | OK (keine Treffer) |

## Klassifikation (Auswahl)

| Datei/Pfad | Einstufung | Grund | Darf Public? | Maßnahme |
| ---------- | ---------- | ----- | ------------ | -------- |
| `backend/core/storage_facade.py` | public_safe | Core-Facade, read-only | ja | wrap existing |
| `backend/core/mount_facade.py` | public_safe | Core-Facade, plan-only | ja | wrap existing |
| `backend/core/safety_facade.py` | public_safe | Core-Facade, write-guard delegation | ja | wrap existing |
| `backend/core/redaction_contract.py` | public_safe | Client-Redaction-Contract | ja | neu (public-safe) |
| `backend/core/telemetry_client_contract.py` | public_safe | Client-Contract ohne Server-URL | ja | neu (public-safe) |
| `backend/core/diagnostic_finding_contract.py` | public_safe | plan-only Finding-Shape | ja | neu (public-safe) |
| `backend/core/audit_event_contract.py` | public_safe | Audit-Envelope ohne Secrets | ja | neu (public-safe) |
| `backend/core/rescue_telemetry_ingest.py` | review_required | Lokaler Dev-Ingest, nicht öffentlicher Telemetrie-Server | ja (mit Review) | private_only Server später |
| `docs/private-handoff/*` | public_safe | Handoff ohne Implementierung | ja | dokumentiert |
| `docs/api/*_openapi.yaml` | public_safe | Stub-Contracts, example domains | ja | dokumentiert |
| `backend/cloudserver_private/` (fehlt) | blocked_from_public_git | proprietär | nein | nur privates Repo |
| `backend/telemetry_server/` (fehlt) | blocked_from_public_git | intern | nein | nur privates Repo |
| `backend/operator_dashboard/` (fehlt) | blocked_from_public_git | intern | nein | nur privates Repo |
| `./.env` | blocked_from_public_git | lokale Secrets | nein | nie committen |
| `commercial/`, `licensing/`, `billing/` (fehlen) | private_only | kommerziell | nein | Handoff only |

## Import-Gate Review (Exit 20)

Rescue-Dateien mit direktem `lsblk` ohne Facade-Delegation (Warnung, kein Block):

- `backend/core/rescue_fat32_esp_*`
- `backend/modules/rescue_restore_*`
- `backend/deploy/runner_rescue_stick_readonly_build_emulation.py`
- `app.py` Zeilenzahl > 12000

**Maßnahme:** Migration auf Core-Facades in separatem Monolith-Facade-Set (nicht in diesem Auftrag).
