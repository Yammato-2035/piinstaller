# Offene Punkte / Fehlliste (Stand: Sanierungslauf)

## 1. Suchfunktion

| Prüfung | Ergebnis |
|---------|----------|
| Vorhanden im Theme-Header? | **Ja** — `header.php`: Formular `GET` auf `home_url('/')` mit Parameter `s` (WordPress-Standard). |
| Styling | `style.css`: `.site-search` (Desktop rechts, mobil volle Breite unter der Leiste). |
| Hinweis | Ergebnisse nutzen die Theme-`search.php`, falls vorhanden — sonst `index.php`-Fallback von WordPress. |

## 2. Startseite / Container / Ränder

| Prüfung | Ergebnis |
|---------|----------|
| Anpassung | `.container` von **1200px** auf **min(1520px, …)** verbreitert; kleine Viewports: engeres Padding. |
| Restrisiko | Sehr breite Monitore: Inhalt nutzt max. 1520px — bewusst für Lesbarkeit; bei Bedarf weiteres Theme-Token möglich. |

**Update:** Suchfunktion und Breitenanpassung umgesetzt — siehe `responsive_width_check.md` und `header.php`.

## 3. Bilder / Screenshots

| Prüfung | Ergebnis |
|---------|----------|
| Pflicht-Screenshots | `screenshot-dashboard.png`, `screenshot-diagnose.png`, `screenshot-projects.png` **vorhanden** (Diagnose/Projects als Alias-Kopien). |
| `hero-product-composition.png` | Erzeugt aus **Foto + echtem** Dashboard-PNG — keine Fake-UI. |

## 4. Sonstiges

- Einzelne Unterseiten (z. B. einzelne Doc-Snippets) nutzen noch **Lucide** im Masthead — funktional gerendert, nicht als „Hero nur Icon“ auf den Kernseiten (Start, Download, Tutorials, Doku, Community, Projekte, Über, Medienserver-Projekt angepasst).
