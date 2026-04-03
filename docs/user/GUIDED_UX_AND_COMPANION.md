# Geführte Nutzung, Erfahrungslevel und Begleiter (SetupHelfer)

Diese Seite ergänzt das **Handbuch in der App** (Dokumentation) und die **FAQ**. Sie fasst zusammen, wie Einsteiger und Fortgeschrittene geführt werden und welche Rolle die **Panda-Begleiter** spielen.

## Erfahrungslevel (Einsteiger / Fortgeschritten / Entwickler)

- **Einsteiger:** Reduzierte Seitenleiste (weniger Menüpunkte), klarere nächste Schritte auf dem **Dashboard**, geführte Bereiche bei **Backup**, **App Store** und anderen Modulen. Umschalten unter **Einstellungen**.
- **Fortgeschritten:** Volle Seitenleiste mit Modi (Allgemein / Erweitert / Diagnose), alle Module sichtbar.
- **Entwickler:** Wie fortgeschritten; zusätzlich entwicklernahe Einträge (z. B. Mailserver/Dev), Panda-Hilfen können ausgeblendet sein.

Die Auswahl wird serverseitig im **Benutzerprofil** gespeichert (`/api/user-profile`). Bei Schreibproblemen unter `/etc/` wird ein Fallback unter `~/.config/pi-installer/` genutzt.

## Panda-Begleiter und Bilder

- **PandaCompanion / PandaRail / PandaHelperStrip:** Kontextbezogene Hinweise (z. B. Backup, App Store, Sicherheit) mit Ampel-Status, wo sinnvoll.
- **Bilder:** Begleiter-Grafiken liegen unter `frontend/src/assets/pandas/` (z. B. install, backup, cloud, debug, docker) und werden je nach Kontext eingebunden.

## Zentrale Modul-Logik (Frontend)

Unter `frontend/src/beginner/moduleModel.ts` sind **ModuleId**, **ExperienceLevel**, **CompanionVariant**, Ampel- und Verfügbarkeitszustände sowie **MODULE_DEFINITIONS** gebündelt – für konsistente Badges („Gesperrt“, „Später“, „Fortgeschritten“) und Texte.

## Dashboard, App Store, Backup (Kurzüberblick)

| Bereich        | Einsteiger-Fokus |
|----------------|------------------|
| **Dashboard**  | Block „Nächster sinnvoller Schritt“, empfohlene Aktionen, spätere/optionale Bereiche gekennzeichnet |
| **App Store**  | Empfohlene Apps zuerst, Hinweise zu fortgeschrittenen oder späteren Apps |
| **Backup**     | Drei Einstiege (erstellen, prüfen, wiederherstellen); erweiterte Tabs unter „Weitere Optionen“ |

## Desktop-Starter

- Schreibtisch: `scripts/desktop-pi-installer-launcher-anlegen.sh` → **SetupHelfer.desktop** (Logo-Icon).
- Auswahl beim Start: **Tauri-App**, **Browser**, **Nur Backend** (`scripts/start-pi-installer.sh`).

## Weitere Dokumentation

- `docs/START_APPS.md` – Startpfade und Desktop-Starter
- `docs/developer/VERSIONING.md` – Versionsschema
- In-App: **Dokumentation** → Kapitel **Dashboard**, **Einstellungen**, **FAQ**
