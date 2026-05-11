# Beitragen zum PI-Installer

Danke für dein Interesse! So kannst du mitmachen.

**Produkt / Branding:** Die Anwendung heißt für Nutzer oft **SetupHelfer**; technische Pfade und Repos können **pi-installer** / `PI-Installer` nutzen – beides ist im Code und in der Doku verbreitet.

## Verbindliche Arbeitsregeln (Cursor / Moduländerungen)

Für **Modulbearbeitungen**, i18n-Pflicht, Nachweise zu Tests, Changelog und Version gilt:

1. **[docs/developer/CURSOR_WORK_RULES.md](docs/developer/CURSOR_WORK_RULES.md)** – zentrales Regelwerk (Phase 0/1: Vorprüfung, keine unnötigen Installationen, Modulvollständigkeit).
2. **[docs/developer/MODULE_EDIT_CHECKLIST.md](docs/developer/MODULE_EDIT_CHECKLIST.md)** – Checkliste zum Abhaken.
3. **[docs/developer/CHANGE_REPORT_TEMPLATE.md](docs/developer/CHANGE_REPORT_TEMPLATE.md)** – Berichtsvorlage für relevante Änderungen.

Details zu Version und Changelog: **[docs/developer/VERSIONING.md](docs/developer/VERSIONING.md)** · Index: **[docs/developer/README.md](docs/developer/README.md)**.

## Ablauf (Fork → Branch → PR)

1. **Fork** das Repository auf GitHub (Button „Fork“).
2. **Klonen** deines Forks und **Branch** für die Änderung:
   ```bash
   git clone https://github.com/DEIN-USERNAME/piinstaller.git
   cd piinstaller
   git checkout -b feature/mein-feature   # oder fix/mein-fix
   ```
3. **Änderungen** vornehmen, **committen** (aussagekräftige Commit-Messages).
4. **Push** in deinen Fork, dann auf GitHub einen **Pull Request** gegen `main` des Upstream-Repos erstellen.
5. Nach Review ggf. nacharbeiten; danach wird gemergt.

## Code & Stil

- **Backend (Python):** Wir nutzen [Ruff](https://docs.astral.sh/ruff/) für Lint; das CI läuft bei jedem Push. Bitte keine unnötigen Warnungen einführen.
- **Frontend (TypeScript/React):** Einheitlicher Stil wie im bestehenden Code (z. B. Komponenten in `src/components/`, API-Calls über `fetchApi`).
- **Versionsnummer:** Nur in `config/version.json` anpassen, danach `cd frontend && node sync-version.js` ausführen (siehe [docs/developer/VERSIONING.md](docs/developer/VERSIONING.md)).

## Issues

- **Bugs:** [Bug-Report-Vorlage](.github/ISSUE_TEMPLATE/bug_report.md)
- **Features:** [Feature-Vorlage](.github/ISSUE_TEMPLATE/feature_request.md)
- **Sicherheit:** Bitte **nicht** als öffentlichen Issue; siehe [SECURITY.md](SECURITY.md).

## Releases & Changelog

Änderungen werden in [CHANGELOG.md](CHANGELOG.md) eingetragen. Bei einem Release wird die Version in `config/version.json` erhöht und ggf. ein GitHub-Release erstellt.
