# Startseite Setuphelfer — Zielstruktur (Umsetzung)

Stand: 2026-03-20  
Quelle: `website/setuphelfer-theme/snippets/index.html`

## Reihenfolge (1–10)

| # | Block | HTML-Anker | Inhalt |
|---|--------|------------|--------|
| 1 | Hero | — | Claim, kurze Lead-Zeile, Badges, CTA Download + Geführter Einstieg, Szene + ein Dashboard-Screenshot |
| 2 | Nutzen / Problem | `#nutzen` | 3 Karten (Problem & Nutzen) |
| 3 | Funktionsübersicht | `#funktionen` | 8 kompakte Feature-Karten |
| 4 | Screenshots + Live | `#screenshots` | 2 Zeilen Produkt-Screenshots, darunter Live-Status (`#setuphelfer-live-status` für JS) |
| 5 | Zielgruppen | `#zielgruppen` | 3 Level-Karten |
| 6 | Tutorials & Hilfe | `#hilfe` | 2 Spalten (Tutorials / Fehlerhilfe) mit bestehenden Illustrationen |
| 7 | Projekte | `#projekte` | 6 Projekt-Karten |
| 8 | Community | `#community` | ein Notice-Block + CTA |
| 9 | Download / CTA | `#download` | `cta-strip` + Sekundärlinks |
| 10 | Footer | — | `footer.php` (nicht im Snippet) |

## Entfernt / zusammengelegt

- „Visuelle Teaser-Bausteine“ (redundant zu Funktion + Hilfe)
- Doppelte Download-/Community-Notices am Ende (zu einem Download-CTA + einer Community-Sektion)
- Separater Sicherheits-`tux-tip`-Block (Link unter Download)
- Hero: keine zweite Screenshot-Zeile mehr (wanderte in Sektion 4)

## Assets

Alle referenzierten Pfade zeigen auf vorhandene Theme-Dateien (`assets/hero`, `assets/screenshots`, `assets/icons`, `assets/illustrations`). Keine unbenannten Platzhalter-Slots.
