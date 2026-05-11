# Installation: Repo, aktive Installation und Legacy-Pfade

Dieses Dokument erklärt, warum auf einem Rechner **mehrere „Versionen“** sichtbar sein können, und wie man den **Ist-Zustand** sicher prüft — **ohne** das Entwicklungsrepo zu löschen.

## Drei Orte, die man unterscheiden muss

| Ort | Zweck | Typische Version |
|-----|--------|------------------|
| **`/home/.../piinstaller`** (Clone dieses Repos) | Entwicklung, `git`, lokale Builds | Entspricht `config/version.json` im Repo; **Tauri-Release unter `frontend/src-tauri/target/release/` muss separat gebaut werden** |
| **`/opt/setuphelfer`** | Aktive **Systeminstallation** (Services, Desktop-Starter) | Entspricht `config/version.json` unter `/opt/setuphelfer` |
| **`/opt/pi-installer`** (Legacy) | Alte PI-Installer-Installation | Historisch; sollte **nicht** mehr aktiv sein. Kann nach **`/opt/pi-installer.archiv-YYYYMMDD`** umbenannt werden (kein Löschen nötig) |

## Warum zeigt Tauri eine „falsche“ Versionsnummer?

- Die Sidebar-Version kommt aus der **gebauten Frontend/Tauri-Binary** (`__APP_VERSION__` aus `package.json` zum Build-Zeitpunkt).
- Startet man **`scripts/start-setuphelfer.sh` aus dem Repo**, wird standardmäßig die **Repo-Tauri-Binary** unter  
  `frontend/src-tauri/target/release/pi-installer` verwendet — nicht automatisch die unter `/opt/setuphelfer`.
- War die Repo-Binary lange nicht neu gebaut, wirkt die Oberfläche „alt“, obwohl `/opt/setuphelfer` bereits neu ist.

**Abhilfe (Entwicklung):** Im Repo `frontend` bauen:

```bash
cd frontend && npm run tauri:build
```

**Abhilfe (nur testen):** System-Starter nutzen:

```bash
/opt/setuphelfer/scripts/start-setuphelfer.sh
```

Das Repo-Skript bricht bei veralteter Repo-Tauri gegenüber `/opt/setuphelfer` nun **mit Hinweis** ab, sofern nicht `SETUPHELFER_ALLOW_OLD_REPO_TAURI=1` gesetzt ist.

Siehe ergänzend: `docs/knowledge-base/BUILD_RUNTIME_CONSISTENCY.md` (Source/Build/Runtime/API-Konsistenz).

## Richtige Startwege (Überblick)

- **Desktop:** `~/Desktop/SetupHelfer.desktop` soll auf `/opt/setuphelfer/scripts/start-setuphelfer.sh` zeigen.
- **systemd (produktiv):** `setuphelfer-backend.service` (API, z. B. `:8000`), `setuphelfer.service` (Web-UI).
- **Legacy:** `pi-installer.service` sollte **maskiert** sein, damit der alte Stack nicht versehentlich startet.

## Audit-Befehl (nur lesen)

Im Repo:

```bash
./scripts/audit-setuphelfer-installations.sh
```

- Exit **0** = `FINAL_VERDICT: OK`
- Exit **2** = `FINAL_VERDICT: WARN` (z. B. noch Referenzen auf `/opt/pi-installer` in Skripten)
- Exit **1** = `FINAL_VERDICT: FAIL` (z. B. aktiver Legacy-Pfad oder Services nicht wie erwartet)

## Umgang mit `/opt/pi-installer` (ohne Löschen)

- **Nicht löschen**, wenn noch Daten oder Nachvollziehbarkeit nötig sind.
- **Reversibel:** Umbenennen nach `/opt/pi-installer.archiv-YYYYMMDD`.
- Vorher prüfen, ob noch **Prozesse** aus diesem Baum laufen (`ps`, `lsof`).

## Tauri LocalStorage / gespeicherte API-URL

Tauri legt WebView-Daten u. a. ab unter:

`~/.local/share/de.pi-installer.app/`

Die App-ID `de.pi-installer.app` ist aktuell ein **historischer Identifier**. Das ist zulässig, muss aber bei Diagnose von Clientzuständen (gespeicherte API-URL, alte UI-Zustände) berücksichtigt werden.

Dort kann u. a. eine gespeicherte Backend-URL liegen (Key `pi-installer-api-base`). Ungültige Ports (z. B. `80000`) führen zu „Server antwortet nicht“, obwohl `setuphelfer-backend` läuft. Die Anwendung bereinigt defekte Werte in neueren Builds; bei Bedarf LocalStorage dort prüfen oder die App neu starten nach Fix.

## Legacy-Service wieder aktivieren (nur falls nötig)

`pi-installer.service` soll im Normalfall **maskiert** bleiben. Rückgängig (nur wenn du weißt, warum):

```bash
sudo systemctl unmask pi-installer.service
sudo cp /etc/systemd/system/pi-installer.service.before-mask.YYYYMMDD /etc/systemd/system/pi-installer.service
sudo systemctl daemon-reload
```

(Alternativ die passende `pi-installer.service.backup.*`-Datei verwenden.)
