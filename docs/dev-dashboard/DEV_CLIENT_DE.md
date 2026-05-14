# Setuphelfer Dev Cockpit — separater Client (Roadmap)

**Kurzfristig (jetzt):** Die Seite `/dev-dashboard` im bestehenden Web-Frontend (Sidebar nur im Entwickler-Profil). Die API `GET /api/dev-dashboard/status` akzeptiert optionale Query-Parameter `frontend_build_version` und `frontend_runtime_source`, damit Backend und UI dieselbe Konsistenz-Ansicht berechnen können, ohne `__APP_VERSION__` allein als Wahrheit zu verwenden.

**Mittelfristig:** Eigenes Tauri-Fenster „Setuphelfer Dev Cockpit“, das nur lokal startet und ausschließlich Developer-APIs anspricht. Kein Ersatz für den normalen Setuphelfer-Desktop; kein Produkt-„grün“.

**Langfristig:** Workspace-Client für mehrere Projekte (generische Dev-Cockpit-Shell), weiterhin ohne privilegierte Schreibpfade und ohne Backup/Restore-Start aus dem Cockpit.

## Sicherheit und Betriebsmodus

- Zugriff nur lokal / Developer Mode; keine Erweiterung der Produkt-Oberfläche für Endanwender.
- Schreibaktionen bleiben `confirm_required` oder `not_implemented_safe` (siehe Platzhalter-POSTs unter `/api/dev-dashboard/actions/*`).
- Optional: Umgebungsvariable `SETUPHELFER_DEV_WORKSPACE_ROOT` setzen, wenn die API aus `/opt/setuphelfer` läuft, die Workspace-Version und Git-Status aber aus einem Checkout unter z. B. `/home/.../piinstaller` gelesen werden sollen.

## API-Basis

Die bestehende `fetchApi`-Logik (localStorage `pi-installer-api-base`) bleibt die konfigurierbare API-Basis; das Dev-Dashboard zeigt die gewählte Basis in der Karte „Runtime vs. Workspace“ an.

## Deploy-Drift (read-only)

Die Status-API enthält `deploy_drift` mit Ampel **green**/**yellow**/**gray** (Dateiabweichungen sind **gelb**, kein automatisches „rot“ aus Drift-Checks). Vorgeschlagene Aktionen sind reine Text-Hinweise (Deploy/Restart/Rebuild), **ohne** automatische Ausführung.

## Deployment-Manifest

- Generator: `backend/tools/generate_deploy_manifest.py` (ohne sudo; Standardausgabe `build/deploy/setuphelfer-deploy-manifest.json`, liegt unter `build/` und ist git-ignoriert).
- Logik/Whitelist: `backend/core/deploy_manifest.py`; Runtime liest optional Manifest unter `build/deploy/` oder `deploy/` relativ zu `/opt/setuphelfer`.
