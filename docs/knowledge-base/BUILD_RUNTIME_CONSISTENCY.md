# Build-/Runtime-Konsistenz (Setuphelfer)

Dieses Dokument beschreibt, wie **Source**, **Frontend-Build**, **Tauri-Binary**, **Runtime** und **Client-Konfiguration** zusammenpassen muessen, damit vor Hardwaretests kein Versions- oder URL-Mismatch auftritt.

## Single Source of Truth: Version

- Primäre Quelle ist `config/version.json` im Repo.
- `frontend/sync-version.js` synchronisiert diese Version in:
  - `frontend/package.json`
  - `frontend/src-tauri/tauri.conf.json` (Semver-kompatibel)
  - `frontend/src-tauri/Cargo.toml` (Semver-kompatibel)
  - `VERSION`
  - Root-`package.json`
- Das Backend liest die Version weiterhin aus `config/version.json` und liefert sie über `/api/version`.

## Source vs. Build vs. Runtime

- **Source (Dev):** `/home/volker/piinstaller`
  - Enthält aktuellen Code, aber noch keine Aussage über laufende Produktion.
- **Frontend-Build:** `frontend/dist`
  - Wird mit `cd frontend && npm run build` erzeugt.
  - Muss zeitlich zu `frontend/src` passen.
- **Tauri-Binary (Repo):** `frontend/src-tauri/target/release/pi-installer`
  - Wird mit `cd frontend && npm run tauri:build` erzeugt.
  - Muss neuer/gleich aktuell wie relevante Dateien in `frontend/src` und `frontend/src-tauri` sein.
- **Aktive Runtime:** `/opt/setuphelfer`
  - Systemdienste laufen von dort (`setuphelfer-backend.service`, `setuphelfer.service`).

## API-Version (`/api/version`)

Die API liefert mindestens:

- `status`
- `version`
- `app_name`
- `tauri_app_id`
- `install_profile`
- optional `app_edition`

Damit ist ein robuster Abgleich zwischen UI-Build-Version (`__APP_VERSION__`) und Backend-Version moeglich.

## Frontend-Client: API-URL und LocalStorage

- Bekannter Key fuer API-Basis: `pi-installer-api-base` (historischer Name, weiterhin kompatibel).
- Standard fuer lokale Runtime:
  - Tauri: `http://127.0.0.1:8000`
  - Browser-Dev: gleiche Origin/Proxy.
- Neue UI-Validierung:
  - prueft beim Start `/api/version`
  - zeigt Warnung bei Nicht-Erreichbarkeit oder Versionsmismatch
  - bietet gezieltes Zuruecksetzen der gespeicherten API-URL auf Standard
  - loescht **nicht** pauschal alle LocalStorage-Daten

## Historische App-ID

- Der Tauri-Identifier ist derzeit `de.pi-installer.app` (historisch).
- Datenpfad daher typischerweise: `~/.local/share/de.pi-installer.app/`.
- Das ist kein automatischer Fehler, aber muss bei Diagnose und Migrationsfaellen bekannt sein.

## Audit / Schnellpruefung

```bash
cd /home/volker/piinstaller
bash -n scripts/*.sh
./scripts/audit-setuphelfer-installations.sh
curl -s http://127.0.0.1:8000/api/version
```

Erwartung:

- kein funktionaler Legacy-Pfad unter `/opt/pi-installer` im Code/Skripten
- `/api/version` konsistent zu `config/version.json`
- `frontend/dist` und Repo-Tauri-Binary nicht veraltet
- `FINAL_VERDICT: OK` (oder maximal begruendetes WARN ohne Funktionsrisiko)

## Typische Fehlerbilder

- **UI zeigt alte Version, Backend korrekt**
  - meist veraltetes `frontend/dist` oder veraltete Repo-Tauri-Binary.
- **Backend korrekt, UI falsch verbunden**
  - gespeicherte API-URL zeigt auf falschen Host/Port.
- **Repo-Binary alt gegenueber `/opt`**
  - `scripts/start-setuphelfer.sh` blockiert Tauri-Start im Repo korrekt.
- **LocalStorage verweist auf alten Kontext**
  - Warnung in UI; gezielt API-URL zuruecksetzen statt globales Loeschen.
