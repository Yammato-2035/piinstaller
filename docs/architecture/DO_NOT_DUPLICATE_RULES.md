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
19. **Keine lsblk/findmnt/blkid-Discovery in `app.py`** — nur `storage_discovery` (+ dokumentierte Legacy-Wrapper); blkid mit sudo nur über `discover_device_fstype(sudo_runner=…)` am Clone-Callsite (P.3).
20. **Kein `import app` in `system_status_core`** — Security/Updates/Realtest nur über `system_status_providers` (G.14).
21. **Keine Backup-GET-Routen neu in `app.py`** — readonly Inventory über `backup_readonly` Router (B.2).
19. **Keine neue Systemstatus-Aggregation** außerhalb `system_status_facade` (G.1+).
20. **Keine Netzwerkdiagnostik** in System Status Facade — nur `network_info_facade` (G.2+).
21. **Keine neue Netzwerkstatus-Aggregation** außerhalb `network_info_facade` (G.2+).
22. **Keine Netzwerk-Schreiboperationen** in Status-Facades — aktive Reparatur nur über späteres eigenes Modul.
23. **Keine neue Ampel-/Traffic-Light-Normalisierung** außerhalb `frontend/src/viewmodels/statusViewModel.ts` (H.1+).
24. **UI-Komponenten** dürfen Status nur darstellen — Normalisierung über ViewModel, nicht inline in Komponenten (H.2+).
26. **Domain-Status** (Partition/Safety/Backup) bleibt lokal bis Domain-Facade — Guard `frontend_domain_status_mapping_requires_domain_facade` (H.4+).
27. **Frontend-Status-Slices H.3–H.7 abgeschlossen** — verbleibende 10 Mappings nur Domain/Large-Page; kein H.8.
28. **Keine neuen Network-GET-Handler in `app.py`**, wenn `api/routes/network.py` existiert — nur Facade-Delegation (G.4+).
29. **Keine Network-Discovery-Implementierung außerhalb `network_info_facade` / geplantem `network_discovery`** — Legacy in `app.py` nur bis G.8 (G.5+).
30. **Keine Webserver-Status-Aggregation außerhalb `webserver_status_facade`** — Network/Port nur über `network_info_facade` (G.7+).
31. **Keine System-Info-Aggregation außerhalb `system_info_facade`** — Network nur über `network_info_facade`; Hardware über `hardware_discovery` (G.6/G.9+).
32. **Keine Hardware-Discovery-Implementierung außerhalb `hardware_discovery`** — `app.py` nur Legacy-Wrapper (G.9+).
33. **Keine Network-Discovery-Implementierung außerhalb `network_discovery`** — `app.py` nur Legacy-Wrapper (G.8+).
34. **Keine Webserver-Service-Discovery außerhalb `webserver_service_discovery`** — `webserver_status_facade` nur Delegation (G.11+).
35. **Keine Ampel-Berechnung außerhalb `system_status_core`** in System-Status-Pfad — Facade nur Aggregation (G.12+).
36. **Keine lsblk/findmnt/blkid-Discovery außerhalb `storage_discovery`** — Facades delegieren (P.1+); Low-Level in `storage_detection`/`mount_facade`.
37. **Keine direkten `detect_block_devices`/`detect_filesystems` aus `storage_detection` in neuen Modulen** — nur über `storage_discovery` (P.1+).
38. **Keine System-Status-Facade→app-Imports** — Runtime/Installation/Profil nur über `system_runtime_info` (G.13+).
39. **Keine inline lsblk/findmnt in `app.py` für Inventar** — delegieren an `storage_discovery` (P.2+).

## Prüfreihenfolge (Cursor)

1. [MODULE_CATALOG.md](MODULE_CATALOG.md)
2. [FUNCTION_OWNERSHIP_MATRIX.md](FUNCTION_OWNERSHIP_MATRIX.md)
3. Diese Datei
4. [MONOLITH_DECOMPOSITION_ROADMAP.md](MONOLITH_DECOMPOSITION_ROADMAP.md)

## Enforcement

`scripts/check-module-boundaries.sh` — WARN-only für Duplikat-Muster und fehlende Katalog-Dateien.
