# Deploy Setuphelfer Identifier Hotspot Cleanup Cycle (DE)

Zyklus 2 nutzt `legacy_identifier_hotspot_analysis.json` (`recommended_next_cleanup_targets`) und kreuzt mit `setuphelfer_safe_rewrite_plan.json` (nur `write_allowed: true`). Referenz: `compatibility_aliases.json` (read-only Kontext, keine automatischen Schreibwege).

**Plan** (`setuphelfer_identifier_cleanup_cycle_2_plan.json`): nur **critical** und **high**, kein **unknown**-Cluster, keine Pfade unter `docs/evidence/`, `docs/history/`, `legacy-backups/`, keine Binaerdateien, max. **50** geplante Eintraege, Rest in `deferred_entries`. Prioritaet: env_config critical → api critical → backend_runtime critical → tauri critical → frontend_runtime critical → scripts high → packaging high.

**Apply** (`setuphelfer_identifier_cleanup_cycle_2_result.json`): nur Plan-Eintraege; Backup je Datei unter `legacy-backups/`; Ersetzungen laengere `legacy_token` zuerst pro Datei; atomisch `.tmp` → `replace`.

**Postcheck** (`setuphelfer_identifier_cleanup_cycle_2_postcheck.json`): Inventory, Identifier-Consistency, erneute Hotspot-Analyse; Zaehler fuer Resttreffer und critical/high.

Keine Runtime, keine Services, kein chmod/chown/systemctl, kein Loeschen, Version **1.7.0**.

API:

- `POST /api/deploy/setuphelfer-identifier-hotspot-cleanup-cycle-plan`
- `POST /api/deploy/setuphelfer-identifier-hotspot-cleanup-cycle-apply`
- `POST /api/deploy/setuphelfer-identifier-hotspot-cleanup-cycle-postcheck`

Codes je `…_OK`, `…_REVIEW_REQUIRED`, `…_BLOCKED`.

## FAQ (Kurz)

- **Warum Cycle 2 hotspot-basiert?** Nur Pfade, die die Hotspot-Analyse priorisiert hat, werden mit dem Safe-Plan abgeglichen — kein Blind-Replace ueber das ganze Repo.
- **Warum nur critical/high?** Mittlere/niedrige Treffer sind bewusst weniger risikoreich und bleiben fuer spaetere Runden.
- **Warum kein Unknown-Auto-Fix?** Unklare Cluster sind manuell zu klassifizieren; automatische Aenderungen waeren unsicher.
- **Warum max. 50?** Kleinere Hotspot-Batches begrenzen Review-Aufwand und Rollback-Komplexitaet.
