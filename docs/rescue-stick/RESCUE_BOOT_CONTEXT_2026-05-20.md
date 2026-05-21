# Rescue Boot Context (Phase C.1)

**Stand:** 2026-05-20  
**Modul:** `backend/rescue/boot_context.py` → `build_rescue_boot_context()`

---

## Zweck

Read-only Klassifikation der Laufzeitumgebung für Rettungsstick-Orchestrierung. **Keine** Mounts, Schreibaktionen, `apt`, `systemctl` oder Geräteänderungen.

## Signale (kein Einzel-Env als alleinige Wahrheit)

- Explizite Hints (`rescue_mode_hint`, `live_system_hint`, …)
- Optional `mount_snapshot` (fstype/target aus findmnt-Handoff)
- `/etc/os-release` (Debian-Live-Hinweise)
- Env `SETUPHELFER_RESCUE_MODE` / `SETUPHELFER_LIVE_SYSTEM` nur ergänzend

## Envelope

| Feld | Werte |
|------|--------|
| `status` | `ok` \| `review_required` \| `blocked` |
| `boot_context` | `live_system`, `rescue_mode`, `source_root`, `runtime_root`, `evidence_root`, `ui_mode`, `network_available`, `allowed_write_roots`, `forbidden_write_roots` |
| `warnings` / `errors` | Listen, immer vorhanden |

## API (Plan only)

`POST /api/deploy/rescue/boot-context/preview`  
Codes: `DEPLOY_RESCUE_BOOT_CONTEXT_{OK|REVIEW_REQUIRED|BLOCKED}`

## Abgrenzung

- Keine ISO-Reife, keine Hardware-Reife
- Ausführung von Backup/Restore/Mount bleibt in Core + `tools/backup_runner.py`
