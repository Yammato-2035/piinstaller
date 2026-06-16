# Monolith-Kandidaten — Priorisierte Großdateien

**Datum:** 2026-06-16  
**Methode:** Zeilenzählung (`wc -l`), Verantwortlichkeiten aus Modul-Docstrings, Import-Fan-in (`rg`), Routen-Dekoratoren  
**Legende Risiko:** hoch = Änderungen breit regressionsanfällig; mittel = fachlich gekapselt aber groß; niedrig = begrenzte Fan-in

| Datei | Zeilen | Bereich | Verantwortlichkeiten | Risiko | Empfehlung | Public/Private-Relevanz |
|-------|--------|---------|----------------------|--------|------------|-------------------------|
| `backend/app.py` | 15.142 | Backend / API | FastAPI-App, ~162 `@app`-Routen, Lifespan, CORS, Rate-Limit, Backup/Restore/Partition/Network/Monitoring-Endpunkte, direkte `storage_discovery`- und `safe_device`-Aufrufe, Audit-DB, Notification-Settings | **hoch** | Schrittweise Router-Slices nach `api/routes/`; verbleibende Routen in Domänenmodule; `app_bootstrap` weiter nutzen | **Public** — produktive `/api/*`-Oberfläche; Private-Logik nur über Facades exponieren |
| `backend/deploy/routes.py` | 3.704 | Deploy / DCC | ~165 `@router`-Routen, Deploy-Runner-Orchestrierung, Hardware-Gates, Rescue-Build-Handoffs, Evidence-Exports, Real-Write-Guard-Anbindung | **hoch** | Runner-Registry beibehalten; HTTP-Schicht in thematische Subrouter splitten (`deploy/routes/`) | **Private** — Development Control Center / Lab; nicht Release-Frontend |
| `frontend/src/pages/BackupRestore.tsx` | 3.992 | Frontend / Backup | Vollständiger Backup-&-Restore-Workflow UI: Zielwahl, Jobs, Tar/RSYNC, Evidenz-Panels, Preflight, i18n-gebundene Statusanzeigen | **hoch** | In Hooks + Subkomponenten (`backup/`, `restore/`) zerlegen; API nur über `api.ts` / dedizierte APIs | **Public** — zentrale Nutzerfunktion |
| `backend/tools/backup_runner.py` | 1.583 | Backend / CLI | Tar/rsync-Backup-Ausführung, sudo-Gates, Exclude-Profile, Evidenz-Schreiben, Exit-Code-Mapping | **mittel** | Als Bibliothek unter `core/backup_execution/` extrahieren; CLI dünn halten | **Public** (indirekt) — wird von Service/Operator aufgerufen; keine HTTP-API |
| `backend/modules/control_center.py` | 1.990 | Backend / Companion | Companion-Dashboard-Daten: Systemstatus, Module, OLED/Monitoring-Aggregation, Read-only-API-Unterstützung | **mittel** | Bereits teilweise über `api/routes/control_center_readonly.py`; Business-Logik nach `core/control_center_facade` | **Public** — Companion-UI (`ControlCenter.tsx`) |
| `backend/core/rescue_fat32_esp_usb_writer.py` | 1.475 | Backend / Rescue | FAT32/ESP-USB-Stick-Schreiben, Partitionierung, GRUB/EFI-Branding, Operator-Selektion, Verify-Hooks | **hoch** | Phasen in `rescue/usb_write/` trennen; Writer vs. Verify vs. Branding | **Public** (Rescue-Produkt) — Hardware-Schreibpfad mit Safety-Gates |
| `backend/core/dev_dashboard.py` | 1.217 | Backend / DCC | Dev-Dashboard-Status, Deploy-Drift-Hinweise, Backup-Target-Preview, Fleet/Rescue-Metadaten, Roadmap-Anbindung | **mittel** | Weitere Delegation an `dev_dashboard_status_service`, `dcc_status_facade` (Fan-in ~23) | **Private** — nur Dev-/Lab-Profil |
| `backend/core/dev_dashboard_cockpit.py` | 731 | Backend / DCC | Cockpit-spezifische Aggregation: kompakte Statusblöcke, Deploy-Drift-Summary, Health-History für Standalone-Fenster | **mittel** | Mit `dev_dashboard_compact_status` zusammenführen oder als reine View-Schicht belassen | **Private** — Tauri-Cockpit / DCC |
| `backend/core/safe_device.py` | 993 | Backend / Safety | Write-Target-Validierung, Mount-Quellenauflösung, Systemdisk-Schutz, Diagnose-IDs (`STORAGE-PROTECTION-*`) | **hoch** | Nur über `safety_facade` importieren (Fan-in ~13 direkt); Legacy-Pfade in `app.py`/`storage_detection` abbauen | **Public** — sicherheitskritische Verträge |
| `backend/core/storage_facade.py` | 623 | Backend / Storage | Kanonische Storage-Snapshot-API, Kandidaten für Backup-Ziele, Discovery-Diagnostics-Bündelung | **mittel** | Behalten als Facade; direkte `storage_discovery`-Nutzung außerhalb der Facade reduzieren | **Public** — Read-only Storage-API für UI und Rescue |

## Ergänzende Kandidaten (Schwellenwert >2.000 Zeilen Frontend)

| Datei | Zeilen | Bereich | Kurzbewertung |
|-------|--------|---------|---------------|
| `frontend/src/pages/ControlCenter.tsx` | 2.681 | Frontend | Spiegel zu `control_center.py`; Split in Companion-Panels empfohlen |
| `frontend/src/pages/InspectRun.tsx` | 2.385 | Frontend | Diagnostics/Inspect-Monolith; an `diagnosticsApi` koppeln |
| `frontend/src/pages/Dashboard.tsx` | 2.291 | Frontend | Legacy-Dashboard; Traffic-Light über `statusViewModel` |
| `scripts/check-module-boundaries.sh` | 1.976 | Scripts | Governance-Gate, kein Laufzeit-Monolith |

## Priorisierung (Umsetzungsreihenfolge)

1. **`app.py` + `deploy/routes.py`** — höchste kombinierte HTTP-Oberfläche und Testlast.
2. **`BackupRestore.tsx`** — größter Public-UI-Monolith.
3. **`safe_device` / `safety_facade`** — Safety-Vertrag vor weiterem Split sichern.
4. **Rescue-Writer** — isolierter Hardware-Pfad, hohes Schadenspotenzial bei Refactor ohne Tests.
5. **DCC-Cluster** (`dev_dashboard*`) — Private; kann parallel zu Public-Splits erfolgen.
