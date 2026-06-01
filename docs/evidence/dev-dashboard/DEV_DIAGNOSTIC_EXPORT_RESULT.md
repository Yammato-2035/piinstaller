# Development Diagnostic Export — Ergebnis

**Stand:** 2026-06-01 · **HEAD:** nach Implementierung

## Umgesetzt

| Bereich | Status |
|---------|--------|
| Contract | `docs/architecture/DEV_DIAGNOSTIC_EXPORT_CONTRACT.md` |
| Backend service | `backend/core/dev_diagnostic_export.py` |
| API | `GET /api/dev-diagnostics/qemu-smokes/{run_id}/export` (+ markdown, evidence-index, fleet-session, latest) |
| Frontend API | `frontend/src/api/devDiagnosticsApi.ts` |
| UI | `LabSessionsPanel` — Copy Summary / JSON / Markdown, Evidence paths |
| Tests | `test_dev_diagnostic_export_v1.py`, `test_dev_diagnostic_export_api_v1.py` — **15 passed** |

## Live-API (`127.0.0.1:8000`)

**Pending (2026-06-01):** Produktives Backend unter `/opt` liefert `404` auf `/api/dev-diagnostics/*` — Router noch nicht deployt. Workspace-Export per Python verifiziert (081222).

Nach Operator-Deploy + Backend-Restart:

```bash
curl -sS "http://127.0.0.1:8000/api/dev-diagnostics/qemu-smokes/qemu_rescue_developer_autopilot_20260601_081222/export" | jq .
```

## Lauf 081222 (erwarteter Export)

- `classification.primary`: `serial_empty_boot_unknown`
- `serial_size_bytes`: `0`
- `report_new`: `false`
- `guest_found`: `false`
- `redacted`: `true`

## Guardrails

- Kein QEMU, ISO, USB, Backup, Restore, apt, Push.
