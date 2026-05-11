# Hero Rework — Selbstprüfung (Prüfliste 1)

| Frage | Ergebnis | Anmerkung |
|-------|----------|-----------|
| Echte Hero-Section vorhanden? | **Ja** | `snippets/index.html` → `<section class="home-hero hero hero--home">`; H1 nennt explizit Plattform für Raspberry Pi und Linux-Einsteiger. |
| Reale oder realitätsnahe Bilder? | **Ja** | Zentral: `{{TAURI_SHOT:screenshot-dashboard.png|…}}` (echter Screenshot). Seitlich: `assets/hero/hero-pi-desktop.svg`, `assets/hero/hero-tux-linux-laptop.svg` (vorhandene Theme-Assets, stilisiert aber sachlich). |
| Raspberry Pi, Linux/Tux, Laptop sichtbar? | **Ja** | Pi-Szene links, Tux/Laptop rechts, Laptop-Mockup mit App in der Mitte. |
| Zwei klare Buttons? | **Ja** | „Geführter Einstieg“, „Installer herunterladen“. |
| Kurzer Markenhinweis? | **Ja** | `<p class="home-brand-notice small">` direkt unter der Hero-Grid. |
| Wirkt wie Produkt, nicht Platzhalter? | **Ja** | Kombination aus Screenshot-Mockup und Szenen-Grafiken; kein reines Icon-Raster. |

**Betroffene Dateien:** `snippets/index.html`, `style.css` (`.hero-composition`, `.home-brand-notice`, Responsive).

**Offen:** Keine fotorealistischen Rohfotos im Repository; falls gewünscht, später unter `assets/images/` ergänzen und `<img>`-Pfade anpassen.
