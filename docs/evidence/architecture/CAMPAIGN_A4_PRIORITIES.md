# Kampagne A.4 — Prioritätenliste (Empfehlung)

Nach Abschluss von A.3 (uncommitted auf `8940213`).

## Reihenfolge nächste 5 Phasen

| # | Phase | Fokus | Risiko |
|---|-------|-------|--------|
| 1 | **P.3** | `app.py` clone/blkid + `_find_lsblk_by_*` vollständig über `storage_discovery`; sudo-Pfad dokumentieren | mittel |
| 2 | **E.11** | `GET /api/dev-dashboard/status` → dünner Router + Facade (BACKUP_JOBS-Adapter) | mittel |
| 3 | **D.14** | Rescue plan_only Batch 2 (~20 Routen) → `routes_rescue_readonly.py` | niedrig |
| 4 | **B.2** | Backup readonly router (`status`, `settings`, `list`, `jobs`) | mittel |
| 5 | **G.14** | `system_status_core` Security/Updates-Adapter ohne `import app` | hoch |

## Begründung

1. **P.3** schließt den größten verbleibenden Storage-Duplikat-Block in `app.py` ab.
2. **E.11** reduziert `app.py` um die komplexeste DCC-GET-Route.
3. **D.14** setzt Thin-Orchestrator ohne Execute-Risiko fort.
4. **B.2** bereitet den zweitgrößten Monolithen (Backup) strukturiert vor.
5. **G.14** beseitigt den letzten kontrollierten `import app` im Status-Pfad.
