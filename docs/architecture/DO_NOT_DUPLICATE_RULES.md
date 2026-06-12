# Do-Not-Duplicate Rules

Verbindliche Regeln gegen parallele Implementierungen. **Keine Ausnahme** ohne dokumentierte Begründung in Evidence.

1. **Keine neue Storage-Erkennung** außerhalb `storage_facade` (Low-Level nur in Boundary-Allowlist).
2. **Keine neue blkid-/lsblk-/findmnt-Logik** außerhalb `storage_facade` / `mount_facade` bzw. dokumentierter Allowlist.
3. **Keine neue Write-Target-Prüfung** außerhalb `safety_facade`.
4. **Keine neue Mount-Planung** außerhalb `mount_facade`.
5. **Keine neuen Runner-Statuswerte** außerhalb `runner_result_contract`.
6. **Keine neue Runner-Risikologik** außerhalb `runner_risk_gate`.
7. **Keine neuen Runner-Metadaten** außerhalb `runner_registry`.
8. **Keine neuen Deploy-Runner-API-Zugriffe** außerhalb `runner_api_facade` in Routern.
9. **Keine neuen Plan-Routen direkt in `routes.py`**, wenn eine Subrouter-Domäne existiert oder geplant ist (D.10+).
10. **Keine UI-Ampellogik** ohne zentrales ViewModel/Fassade, sobald diese existiert (PLANNED).
11. **Keine neuen i18n-Großdateien** ohne Namespace-Konzept (`de.json`/`en.json` pro Bereich).
12. **Neue Module** müssen zuerst in [MODULE_CATALOG.md](MODULE_CATALOG.md) als CANDIDATE eingetragen werden.
13. **Keine neuen `/health`- oder `/api/version`-Handler in `app.py`**, wenn `api/routes/health.py` bzw. `version.py` existieren (E.1+).
14. **Keine neuen Settings-/Status-GET-Handler in `app.py`**, wenn `api/routes/settings.py` bzw. `status.py` existieren (E.2+).
15. **Keine neuen DCC-Index-GET in `app.py`**, wenn `dev_dashboard_readonly.py` existiert — Scanner nur in `core.dev_dashboard*` (E.4+).
16. **Keine neuen Roadmap-Registry-GET in `app.py`**, wenn `dev_dashboard_roadmap.py` existiert — Parser nur in `core.dev_dashboard_roadmap` (E.5+).
17. **Keine neue DCC-Statusaggregation in Routern/`app.py`**, wenn `dcc_status_facade` existiert — HTTP-Leser nur über Facade-API-Helper (F.1–F.4).
18. **Keine neue Ampel-/Status-Mapping-Logik** außerhalb `dcc_status_facade` / `system_status_facade` / dokumentiertem ViewModel (F.1+/G.1+).
19. **Keine neue Systemstatus-Aggregation** außerhalb `system_status_facade` (G.1+).
20. **Keine Netzwerkdiagnostik** in System Status Facade — nur `network_info_facade` (G.2+).
21. **Keine neue Netzwerkstatus-Aggregation** außerhalb `network_info_facade` (G.2+).
22. **Keine Netzwerk-Schreiboperationen** in Status-Facades — aktive Reparatur nur über späteres eigenes Modul.

## Prüfreihenfolge (Cursor)

1. [MODULE_CATALOG.md](MODULE_CATALOG.md)
2. [FUNCTION_OWNERSHIP_MATRIX.md](FUNCTION_OWNERSHIP_MATRIX.md)
3. Diese Datei
4. [MONOLITH_DECOMPOSITION_ROADMAP.md](MONOLITH_DECOMPOSITION_ROADMAP.md)

## Enforcement

`scripts/check-module-boundaries.sh` — WARN-only für Duplikat-Muster und fehlende Katalog-Dateien.
