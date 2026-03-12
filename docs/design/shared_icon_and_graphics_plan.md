## Gemeinsamer Icon- und Grafik-Plan (App + spätere Website)

_Ziel: Dokumentierte Grundlage, wie Icons und Grafiken strukturiert und wiederverwendet werden können – ohne neue UI-Funktionen zu bauen._

---

### 1. Zielbild

- **Ein Icon- und Grafiksystem** für:
  - PI-Installer App (React/Tauri)
  - spätere Website (Dokuseiten, Landingpage, Handbuch)
- **Quell-Assets** sollen unabhängig vom Build liegen:
  - App nutzt sie über `/assets/...`
  - Website kann dieselben Pfade referenzieren

---

### 2. Ordnerlogik (nur dokumentiert)

Vorgeschlagene Quellstruktur (kompatibel zu bestehendem Design, ohne aktuelle Nutzung zu brechen):

```text
frontend/public/assets/
  icons/
    navigation/
    status/
    devices/
    process/
    diagnostic/
  illustrations/
    install/
    connect/
    diagnose/
    empty_states/
```

- **App**:
  - `AppIcon` lädt Icons aus `/assets/icons/{navigation,status,devices,process,diagnostic}/...`
  - Leere Zustände und Screenshots können später auf `/assets/illustrations/...` wechseln.
- **Website (später)**:
  - Statische Seiten können dieselben Pfade direkt nutzen (ohne React-spezifischen Code).

> Aktueller Stand: Im Repo sind primär die fertigen Icons unter `frontend/dist/assets/icons/...` sichtbar. Die hier dokumentierte Struktur beschreibt das Ziel – ohne es in dieser Phase technisch umzusetzen.

---

### 3. Rollen der Systeme: AppIcon vs. Lucide

- **AppIcon (SVG aus /assets/icons)**:
  - _Empfohlene_ Domäne:
    - Navigation (Sidebar, Tabs, Seiten-Header)
    - Status (OK/Warnung/Fehler/Aktiv/Running)
    - Geräte (Pi, Laufwerke, Netzwerk, Anzeige, Audio)
    - Prozess-Stufen (Installationsschritte, Scan/Write/Verify)
    - Diagnose-Symbole (Logs, Systemcheck, Debug)

- **Lucide-Icons (`lucide-react`)**:
  - _Empfohlene_ Domäne:
    - Inline-Icons innerhalb von Texten/Karten.
    - Developer-nahe Bereiche (z. B. Code/Tools/Panels).
    - Fälle, wo schnelle Ergänzungen nötig sind und noch kein dediziertes AppIcon existiert.

> In der aktuellen App werden beide Systeme häufig gemischt. Das ist funktional zulässig, aber visuell uneinheitlich. Diese Phase dokumentiert den Zustand und eine Zielaufteilung – Umstellungen erfolgen später, nicht jetzt.

---

### 4. Mapping: Designnamen ↔ Dateien ↔ AppIcon-Namen

Beispiele für konsolidierte Zuordnung:

| Domäne        | Design-Name          | Datei                         | AppIcon `category/name`          |
|---------------|----------------------|-------------------------------|----------------------------------|
| Navigation    | Dashboard            | `navigation/icon_dashboard.svg` | `navigation` / `dashboard`     |
| Navigation    | Installation         | `navigation/icon_installation.svg` | `navigation` / `installation` |
| Navigation    | Einstellungen        | `navigation/icon_settings.svg` | `navigation` / `settings`      |
| Navigation    | Control Center       | `navigation/icon_advanced.svg` | `navigation` / `control-center`|
| Status        | OK                   | `status/status_ok.svg`        | `status` / `ok`                 |
| Status        | Warnung              | `status/status_warning.svg`   | `status` / `warning`            |
| Status        | Fehler               | `status/status_error.svg`     | `status` / `error`              |
| Geräte        | Raspberry Pi         | `devices/device_raspberrypi.svg` | `devices` / `raspberrypi`    |
| Geräte        | WLAN                 | `devices/device_wifi.svg`     | `devices` / `wifi`              |
| Prozess       | Suchen               | `process/process_search.svg`  | `process` / `search`            |
| Prozess       | Schreiben            | `process/process_write.svg`   | `process` / `write`             |
| Diagnose      | Logs                 | `diagnostic/diagnose_logs.svg` | `diagnostic` / `logs`         |

> Diese Zuordnung reflektiert den aktuellen `AppIcon`-Code und die vorhandenen SVG-Dateien. Weitere Tabellen stehen bereits in `icon_usage.md` und `icon_list.md`.

---

### 5. Grafiken und Illustrationen (Empty States)

Laut `graphics_system.md` sind folgende Illustrationen geplant:

- **Empty States (konzeptionell)**:
  - `illus_empty_no_device` – Kein Gerät verbunden.
  - `illus_empty_no_modules` – Keine Apps/Module.
  - `illus_empty_no_errors` – Keine Fehler.
  - `illus_empty_no_network` – Kein Netzwerk.

Aktueller Stand:

- Im Repo sind diese Illustrationen **nicht** als Dateien sichtbar.
- Einige leere Zustände im UI nutzen derzeit nur Text + Icon (teilweise Lucide).

> Für diese Phase: Nur dokumentieren, dass diese Motive vorgesehen sind und später als wiederverwendbare Grafiken unter `frontend/public/assets/illustrations/empty_states/` abgelegt werden können.

---

### 6. Website-Wiederverwendung (nur Plan)

Mögliche spätere Nutzungsformen (keine Umsetzung in dieser Phase):

- Landingpage:
  - Navigation-Icons für Hauptbereiche (Dashboard, Installation, Backup, Control Center).
  - Illustrationen für „Lerncomputer“, „Media“, „Backup“.
- Dokumentationsseite:
  - Status-Icons für Callouts (OK/Warnung/Fehler).
  - Geräte-Icons für Hardware-Kapitel (Pi, Speicher, Netzwerk).

Wichtig:

- Die Website soll **keine** eigenen Icon-Duplikate bekommen.
- Quelle bleibt der gemeinsame Asset-Baum unter `frontend/public/assets/`.

---

### 7. Offene B-Punkte (Icons & Grafiken)

1. **Parallelbetrieb AppIcon / Lucide-Icons**  
   - Status: dokumentiert, stilistisch gemischt.  
   - Risiko: nur visuell, kein Laufzeitfehler.

2. **Fehlende Illustrations-Assets**  
   - Status: in Design-Docs konzipiert, im Repo (noch) nicht vorhanden.  
   - Vorgehen: später als eigenständiges Asset-Projekt behandeln.

3. **Quell- vs. Build-Assets**  
   - Status: Build-Icons liegen unter `frontend/dist/assets/icons`; Quellablage laut Design-Doku unter `frontend/public/assets/...` vorgesehen.  
   - Vorgehen: in späterer technischen Runde klären, wo die „Master“-SVGs liegen sollen.

---

### 8. Selbstprüfung Phase 2 (Shared Icons & Graphics)

- **Wurde funktional etwas erweitert?**  
  - Nein. Es wurden nur Pläne und Mappings dokumentiert.

- **Nur Dokumentation/Struktur?**  
  - Ja. Die Datei beschreibt Zielstruktur und Zuordnungen, ohne Code oder Build-Prozess anzupassen.

- **Website-Nutzung berücksichtigt, ohne Website zu bauen?**  
  - Ja. Mögliche Nutzung ist beschrieben, aber nicht implementiert.

