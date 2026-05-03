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

## Systemstatus-Policy (`/api/system/status`)

Die Ampeln fuer Dashboard/Companion werden nicht mehr statisch gesetzt, sondern aus realen Signalen berechnet:

- `security`:
  - `green`: alle 5 Bausteine aktiv (UFW, Fail2Ban, Auto-Updates, SSH-Haertung, Audit-Logging)
  - `yellow`: mindestens ein Baustein fehlt
  - `red`: kritischer Mangel (z. B. `PermitRootLogin yes` oder Firewall nicht installiert)
- `updates`:
  - `green`: keine Updates
  - `yellow`: nur notwendige/optionale Updates
  - `red`: Security- oder Critical-Updates vorhanden

Wichtig: Dashboard, Security-Begleiter und `/api/system/status` muessen denselben Lampenzustand anzeigen.

## Netzwerk-API (`/api/system/network`)

Die API liefert neben `ips`/`hostname` jetzt zusaetzlich:

- `localhost` (lokale Adresse, aktuell `127.0.0.1`)
- `primary_ip`
- `interfaces` (Quelle/Interface pro erkannter IP)
- `warnings`
- `source` (`ip-addr-global`, `hostname-I`, `none`)

Erkennung:

- Primaer: `ip -4 -o addr show scope global`
- Fallback: `hostname -I`
- Filter: `lo`, `docker*`, `veth*`, `br-*`, `virbr*`, `wg*`, `tailscale*`, Loopback/Link-Local

Wenn keine LAN-IP ermittelt wird, bleibt die API explizit auf "lokal" und liefert eine begruendete Warnung statt leerem/unklarem Zustand.

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
curl -s http://127.0.0.1:8000/api/system/status
curl -s http://127.0.0.1:8000/api/system/network
```

Erwartung:

- kein funktionaler Legacy-Pfad unter `/opt/pi-installer` im Code/Skripten
- `/api/version` konsistent zu `config/version.json`
- `frontend/dist` und Repo-Tauri-Binary nicht veraltet
- `FINAL_VERDICT: OK` (oder maximal begruendetes WARN ohne Funktionsrisiko)

## Update-Start (Einsteiger-Schutz + Tauri-Fallback)

- Einsteigerfluss: "Update im Terminal" zeigt zuerst eine Sicherheitsabfrage mit Option "Spaeter erinnern" (24h).
- Backend-Endpoint `/api/system/run-update-in-terminal` startet ein Terminal nur mit valider GUI-Session.
- Falls Backend im systemd-Kontext keine GUI-Session hat (`DISPLAY/WAYLAND` fehlt), kann die Tauri-App das Terminal lokal ueber einen Tauri-Command starten.
- Ergebnis: kein "falsches Erfolgssignal" mehr, entweder sichtbares Terminal oder klarer manueller Hinweis.

## Typische Fehlerbilder

- **UI zeigt alte Version, Backend korrekt**
  - meist veraltetes `frontend/dist` oder veraltete Repo-Tauri-Binary.
- **Backend korrekt, UI falsch verbunden**
  - gespeicherte API-URL zeigt auf falschen Host/Port.
- **Repo-Binary alt gegenueber `/opt`**
  - `scripts/start-setuphelfer.sh` blockiert Tauri-Start im Repo korrekt.
- **LocalStorage verweist auf alten Kontext**
  - Warnung in UI; gezielt API-URL zuruecksetzen statt globales Loeschen.
