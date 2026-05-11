# Inspect Phase 0/1 (DE)

## Ziel

`/api/inspect/run` liefert eine defensive, read-only Bestandsaufnahme als Rohdaten.
Inspect in Phase 0/1 fuehrt keine Reparatur, kein Restore, kein Deploy und keine Schreiboperationen auf Datentraegern aus.

## Umfang der Datensammlung

- Storage:
  - Blockgeraete via `modules.storage_detection.detect_block_devices`
  - Filesystem-Metadaten via `modules.storage_detection.detect_filesystems`
  - Klassifikation via `modules.storage_detection.classify_devices`
  - Mountbarkeit via `modules.inspect_storage.check_mountability`
  - UUID-Konflikte via `modules.inspect_storage.detect_uuid_conflicts`
- Boot:
  - Bootstatus via `modules.inspect_boot.analyze_boot_status`
- Netzwerk:
  - Netzwerkstatus via `modules.rescue_readonly_analyze._analyze_network`

## API

- Fortsetzung (Interpretation/Empfehlung, weiterhin read-only): `docs/inspect/INSPECT_PHASE_2_DE.md`
- Endpoint: `GET /api/inspect/run`
- **Erreichbarkeit (404 vermeiden):** Die Route wird in `backend/app.py` beim Start registriert. Ein **404** entsteht typischerweise, wenn die laufende Backend-Instanz **älteren Code** ohne Inspect-Router nutzt (z. B. veraltetes `/opt/setuphelfer` nach Deploy-Verzug) oder der Router beim Import fehlschlägt (siehe Log: Meldung zu Inspect-Router). Mit `curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:<PORT>/api/inspect/run` prüfen.
- **Port 8000:** Unter systemd ist oft `setuphelfer-backend.service` alleiniger Listener auf `127.0.0.1:8000` (siehe `systemctl status setuphelfer-backend`). Ein zweites Repo-Backend auf demselben Port startet nicht ohne Konflikt — **keine** Dienste blind beenden; stattdessen z. B. `PI_INSTALLER_BACKEND_PORT=8010 ./scripts/start-backend.sh` und im Frontend `VITE_PROXY_TARGET=http://127.0.0.1:8010` in `frontend/.env.development` (siehe `frontend/.env.development.example`).
- **APP_EDITION:** Der installierte Dienst setzt häufig `APP_EDITION=release` (Endnutzer-Build). Inspect Phase 0/1 ist davon unabhängig erreichbar, solange die **gleiche Codebasis** den Router enthält.
- Antwortstruktur:
  - `system`
  - `storage`
  - `filesystems`
  - `boot`
  - `network`
  - `capabilities`
  - `warnings`
  - `errors`
  - `source_modules`

## Defensive OS-Hinweise (nur Hinweise)

Inspect liefert vorbereitende Hinweis-Flags in `capabilities.os_hints`:

- `possible_linux`
- `possible_windows`
- `possible_dualboot`
- `possible_empty_disk`
- `possible_broken_boot`
- `unknown_layout`

Diese Hinweise sind keine Enddiagnose und keine Freigabe fuer Aktionen.

## Nicht enthalten in Phase 0/1

- keine Ampel-Bewertung
- keine Handlungsempfehlung
- keine Rescue-Freigabe
- keine Restore-/Deploy-Buttons
- keine neue Backup-/Verify-/Restore-/Crypto-Logik
