# Asset-Manifest – Setuphelfer

Datum: 2026-03-20  
Scope: referenzierte Assets aus `snippets/*.html` plus Branding aus `header.php`

Statuswerte:
- `vorhanden`: Datei physisch vorhanden
- `bedingt`: Datei vorhanden, Webauslieferung aber deployment-abhängig
- `fehlt`: referenziert, aber nicht gefunden

## Logos

| Dateiname | Referenzierter Pfad | Tatsächlicher Dateistatus | Verwendet in Komponente |
|---|---|---|---|
| `setuphelfer-logo-main.svg` | `assets/branding/setuphelfer-logo-main.svg` | vorhanden | `header.php` |
| `setuphelfer-favicon.svg` | `assets/branding/setuphelfer-favicon.svg` | vorhanden | `header.php` |
| `setuphelfer-app-icon.svg` | `assets/branding/setuphelfer-app-icon.svg` | vorhanden | `header.php` |

## Hero-Grafiken

| Dateiname | Referenzierter Pfad | Tatsächlicher Dateistatus | Verwendet in Komponente |
|---|---|---|---|
| `hero-setup-scene.svg` | `assets/hero/hero-setup-scene.svg` | vorhanden (GPIO-Detail, A11y-Metadaten) | `index.html` |
| `hero-pi-laptop.svg` | `assets/hero/hero-pi-laptop.svg` | vorhanden | `guided-start.html` |
| `hero-scene-overlay.svg` | `assets/visual-system/hero-scene-overlay.svg` | vorhanden | optional / `asset-slots.json` — Live-Site nutzt echte Screenshots statt Platzhalter-Slots |

## Screenshot-Container (Vector, optional)

| Dateiname | Referenzierter Pfad | Tatsächlicher Dateistatus | Verwendet in Komponente |
|---|---|---|---|
| `screenshot-container-desktop.svg` | `assets/visual-system/screenshot-container-desktop.svg` | vorhanden | `asset-slots.json` (`screenshot_chrome.desktop_window`); optional für Druck/Präsentation — Standard-Website: HTML `.shot-frame` |

## Feature-Illustrationen

| Dateiname | Referenzierter Pfad | Tatsächlicher Dateistatus | Verwendet in Komponente |
|---|---|---|---|
| `section-download-installer.svg` | `assets/illustrations/section-download-installer.svg` | vorhanden | `index.html`, `download.html` |
| `section-tutorials-help.svg` | `assets/illustrations/section-tutorials-help.svg` | vorhanden | `index.html`, `tutorials.html` |
| `section-community-forum.svg` | `assets/illustrations/section-community-forum.svg` | vorhanden | `index.html`, `kontakt.html` |
| `section-security-setup.svg` | `assets/illustrations/section-security-setup.svg` | vorhanden | `index.html`, `troubleshooting.html`, `sicherheit.html` |
| `section-projects-discovery.svg` | `assets/illustrations/section-projects-discovery.svg` | vorhanden | `projects.html` |
| `section-guided-start.svg` | `assets/illustrations/section-guided-start.svg` | vorhanden | `guided-start.html` |

## Icons

| Dateiname | Referenzierter Pfad | Tatsächlicher Dateistatus | Verwendet in Komponente |
|---|---|---|---|
| `icon-system.svg` | `assets/icons/icon-system.svg` | vorhanden | `index.html`, `projects.html`, `download.html`, `tutorials.html`, `troubleshooting.html` |
| `icon-diagnostics.svg` | `assets/icons/icon-diagnostics.svg` | vorhanden | `index.html`, `documentation.html`, `troubleshooting.html` |
| `icon-backup.svg` | `assets/icons/icon-backup.svg` | vorhanden | `index.html`, `tutorials.html`, `documentation.html` |
| `icon-tutorials.svg` | `assets/icons/icon-tutorials.svg` | vorhanden | `index.html`, `tutorials.html` |
| `icon-projects.svg` | `assets/icons/icon-projects.svg` | vorhanden | `index.html`, `projects.html`, `community.html`, `download.html` |
| `icon-community.svg` | `assets/icons/icon-community.svg` | vorhanden | `index.html`, `community.html` |
| `icon-security.svg` | `assets/icons/icon-security.svg` | vorhanden | `index.html`, `troubleshooting.html` |
| `icon-docs.svg` | `assets/icons/icon-docs.svg` | vorhanden | `tutorials.html`, `documentation.html` |
| `icon-docs-guide.svg` | `assets/icons/icon-docs-guide.svg` | vorhanden | `community.html` |
| `icon-docker.svg` | `assets/icons/icon-docker.svg` | vorhanden | `tutorials.html`, `documentation.html` |
| `icon-mailserver.svg` | `assets/icons/icon-mailserver.svg` | vorhanden | `documentation.html` |
| `icon-expert.svg` | `assets/icons/icon-expert.svg` | vorhanden | `index.html` (Lernpfad Experte) |
| `icon-download.svg` | `assets/icons/icon-download.svg` | vorhanden (256×256, konsistent mit Beginner/Advanced) | `asset-slots.json` |
| `ui-warning.svg` | `assets/ui/ui-warning.svg` | vorhanden | `index.html`, `troubleshooting.html`, `issue-*.html` |
| `ui-search.svg` | `assets/ui/ui-search.svg` | vorhanden | `troubleshooting.html` |
| `ui-info.svg` | `assets/ui/ui-info.svg` | vorhanden | `troubleshooting.html` |

## Screenshots

Hinweis (Stand nach Sanierung): In Snippets `assets/screenshots/<datei>.png` (Theme-Auslieferung, Status **vorhanden** auf der Website). Entwicklungs-Quelle zum Abgleich: `docs/screenshots/` bzw. `frontend/public/docs/screenshots/`.

| Dateiname | Referenzierter Pfad | Tatsächlicher Dateistatus | Verwendet in Komponente |
|---|---|---|---|
| `screenshot-dashboard.png` | `assets/screenshots/screenshot-dashboard.png` | vorhanden (Theme) | `index.html`, `download.html`, `documentation.html`, `tutorial-first-setup.html`, `tutorial-linux-basics.html`, `tutorial-network-basics.html` |
| `screenshot-wizard.png` | `assets/screenshots/screenshot-wizard.png` | vorhanden (Theme) | `index.html`, `tutorial-first-setup.html` |
| `screenshot-settings.png` | `assets/screenshots/screenshot-settings.png` | vorhanden (Theme) | `index.html`, `tutorial-first-setup.html`, `tutorial-linux-basics.html` |
| `screenshot-presets.png` | `assets/screenshots/screenshot-presets.png` | vorhanden (Theme) | `index.html`, `download.html`, `documentation.html` |
| `screenshot-security.png` | `assets/screenshots/screenshot-security.png` | vorhanden (Theme) | `index.html`, `download.html` |
| `screenshot-users.png` | `assets/screenshots/screenshot-users.png` | vorhanden (Theme) | `download.html`, `tutorial-linux-basics.html` |
| `screenshot-backup.png` | `assets/screenshots/screenshot-backup.png` | vorhanden (Theme) | `download.html`, `tutorial-backup-basics.html` |
| `screenshot-documentation.png` | `assets/screenshots/screenshot-documentation.png` | vorhanden (Theme) | `index.html`, `download.html`, `documentation.html`, `tutorial-backup-basics.html` |
| `screenshot-control-center.png` | `assets/screenshots/screenshot-control-center.png` | vorhanden (Theme) | `tutorial-backup-basics.html` |
| `screenshot-monitoring.png` | `assets/screenshots/screenshot-monitoring.png` | vorhanden (Theme) | `tutorial-network-basics.html` |
| `screenshot-webserver.png` | `assets/screenshots/screenshot-webserver.png` | vorhanden (Theme) | `tutorial-network-basics.html`, `tutorial-docker-basics.html` |
| `screenshot-devenv.png` | `assets/screenshots/screenshot-devenv.png` | vorhanden (Theme) | `tutorial-docker-basics.html` |
| `screenshot-nas.png` | `assets/screenshots/screenshot-nas.png` | vorhanden (Theme) | `tutorial-docker-basics.html` |

## Dokumentationsbilder

| Dateiname | Referenzierter Pfad | Tatsächlicher Dateistatus | Verwendet in Komponente |
|---|---|---|---|
| `docs.svg` | `assets/images/docs.svg` | vorhanden | `documentation.html` |
| `doc-installation.svg` | `assets/images/doc-installation.svg` | vorhanden | `doc-installation.html`, `doc-installation-issues.html` |
| `doc-backup.svg` | `assets/images/doc-backup.svg` | vorhanden | `doc-backup.html` |
| `doc-diagnostics.svg` | `assets/images/doc-diagnostics.svg` | vorhanden | `doc-diagnostics.html`, `doc-hardware-issues.html` |
| `doc-docker.svg` | `assets/images/doc-docker.svg` | vorhanden | `doc-docker.html` |
| `doc-mailserver.svg` | `assets/images/doc-mailserver.svg` | vorhanden | `doc-mailserver.html` |

## Defekt-/Fehlbestand (manifestrelevant)

- Kein physisch fehlendes Bild/Icon im Theme gefunden.
- Screenshot-Pfade sind nicht mehr vom Webroot `/docs/...` abhängig; Auslieferung erfolgt mit dem Theme unter `assets/screenshots/`.
