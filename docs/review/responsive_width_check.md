# Responsive / Containerbreite — Prüfliste 7

## Änderung

- **Datei:** `website/setuphelfer-theme/style.css`
- **Vorher:** `.container { width: min(1200px, calc(100% - 40px)); }`
- **Nachher:** `.container { width: min(1520px, calc(100% - 32px)); }` plus `@media (max-width:720px)` mit schmalerem Rand.

## Eigenprüfung

| Frage | Ergebnis |
|-------|----------|
| Größere Bildschirme: weniger „Briefkasten“? | Ja — nutzbarer Content bis ca. 1520px. |
| Mobile geschädigt? | Nicht beabsichtigt — `calc(100% - …)` begrenzt weiterhin. |
| Nur Startseite? | **Nein** — `.container` gilt global (inkl. Header/Main); konsistent mit Ziel „weniger Rand“. |

## Hinweis

`.home-hero` nutzt weiter `100vw` für Vollbreiten-Hintergrund; unverändert.
