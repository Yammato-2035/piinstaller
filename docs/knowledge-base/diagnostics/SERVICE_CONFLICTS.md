# Service-Konflikte (pi-installer vs. Setuphelfer)

## Problem

Mehrere Installationen (`/opt/pi-installer` und `/opt/setuphelfer`) oder parallele systemd-Units (`pi-installer*.service` und `setuphelfer-backend.service`) konkurrieren um **TCP-Port 8000**. Das verfaelscht API-Tests und ist auf Zielsystemen nicht gewuenscht.

## Erkennung (Backend, lesend)

- Modul: `backend/core/service_conflict_guard.py`
- API: `GET /api/system/service-conflicts` — liefert `conflicts[]`, `port_owner`, `active_services`, `install_paths`, `recommended_actions` (keine Stop-/Disable-Aktionen ueber diese API).
- Preflight: `scripts/start-backend.sh` ruft `port_preflight_main()` auf (Exit **10** = gleicher Stack laeuft bereits, Skript endet **0**; Exit **2** = harter Konflikt).
- Deaktivieren: `PI_INSTALLER_SKIP_SERVICE_CONFLICT_GUARD=1` oder `SETUPHELFER_SKIP_SERVICE_CONFLICT_GUARD=1` (nur fuer bewusste Sonderfaelle).

## Diagnose-IDs

| ID | Kurz |
|----|------|
| SERVICE-CONFLICT-033 | Legacy `pi-installer.service` aktiv |
| SERVICE-CONFLICT-034 | Port 8000 gehoert nicht zur erwarteten Installation (z. B. `/opt/pi-installer` im Listener) |
| SERVICE-CONFLICT-035 | Beide Opt-Baeume vorhanden und Legacy-Units noch enabled/aktiv |
| SERVICE-CONFLICT-036 | Start aus `/opt/pi-installer`, neuere Version unter `/opt/setuphelfer` |

## Installer / postinst

- `debian/postinst`: stoppt/disable **pi-installer**-Units mit Logzeile; **kein** automatisches Loeschen von `/opt/pi-installer`.
- `scripts/install-system.sh`: Downgrade-Schutz (Quelle nicht aelter als Ziel unter `/opt/setuphelfer`, ausser `SETUPHELFER_ALLOW_DOWNGRADE=1`); vor systemd-Aktivierung Legacy-Dienste stoppen/disable.

## Nicht-Ziele

Kein blindes `kill` aus dem normalen API-Request-Pfad, keine Datenmigration, keine Aenderung an Backup-/Restore-Kernlogik.
