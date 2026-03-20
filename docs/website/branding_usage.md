# Branding-Nutzung – setuphelfer.de

_Ziel: Festlegen, wie Branding-Elemente (Name, Farben, Icons, Tux, Raspberry-Pi-Anmutung) auf setuphelfer.de eingesetzt werden, damit sie konsistent mit dem PI-Installer bleiben._

---

## 1. Namens- und Projektdarstellung

- **Projektname:**
  - Website: „SetupHelfer“ als Plattformname.
  - Produkt im Zentrum: „PI-Installer“.
- **Darstellung:**
  - Auf der Startseite sollte klar werden:
    - SetupHelfer = Plattform/Website.
    - PI-Installer = konkreter Installer für Raspberry Pi / Linux-Setup.
- **Vermeidung:**
  - Keine neuen Produktnamen oder Sub-Brands erfinden.

---

## 2. Farb- und Formensprache

- **Primärfarben:**
  - Gleiche Sky-Blau-Akzente wie im PI-Installer.
  - Dunkle Hintergründe für Hauptbereiche, helle/elevated Flächen für Inhalte.
- **Status- und Risiko-Farben:**
  - Entsprechen dem bereits dokumentierten System in den App-Design-Dokumenten.
  - Einheitliche Verwendung in Badges, Hinweisboxen und Statusanzeigen.

---

## 3. Icon-Nutzung

- **Quelle:**
  - Icons aus `frontend/public/assets/icons/`:
    - `navigation`, `status`, `devices`, `process`, `diagnostic`.
- **Einsatz:**
  - Hauptnavigation (z. B. Home, Download, Hilfe).
  - Feature-Karten (z. B. Sicherheit, Backup, Diagnose).
  - Projekt-/Tutorialkarten (z. B. Geräte-Icons, Prozess-Icons).
- **Regeln:**
  - Icons nach Möglichkeit konsistent zu App-Bedeutungen einsetzen (z. B. `status_ok` nur für „OK“).
  - Keine neuen, abweichenden Interpretationen derselben Icons.

---

## 4. Screenshots und Illustrationen

- **Screenshots:**
  - Nutzen dieselben Dateien wie in der Dokumentation/README (zentrale Ablage).
  - Einsatz:
    - Auf Home und Download als Vorschau.
    - In Tutorials/Doku als Schrittbeispiele.
- **Illustrationen:**
  - Onboarding-/Projekt-/Status-Grafiken gemäß `missing_graphics.md`.
  - Einmal produziert, sowohl in App als auch Website einsetzen.

---

## 5. Tux und Raspberry-Pi-Branding

- **Einsatz-Typen:**
  - Tux:
    - Hilft, Linux-Kontext sichtbar zu machen.
    - Besonders in Einsteigerbereichen und Linux-Einführungstexten.
  - Raspberry-Pi-Anmutung:
    - Symbolische Darstellung (z. B. Pi-Silhouette, Board-Form).
    - Einsatz in Hero-Grafik, Projektsektion, nicht als offizielles Logo.

- **Regeln:**
  - Stilistisch an restliche Illustrationen anpassen (Farbe, Strichstärke, Einfachheit).
  - Tux & Pi nicht inflationär – gezielt für Orientierung („Hier geht es um Linux/Pi“).

---

## 6. Tone of Voice (Textstil)

- **Charakter:**
  - Freundlich, ruhig, sachlich.
  - „Du“-Ansprache für Einsteiger; klare, kurze Sätze.
- **Vermeidung:**
  - Keine aggressive Marketing-Sprache.
  - Keine Übertreibungen oder Versprechen, die der PI-Installer nicht hält.
- **Bezug zum Installer:**
  - Formulierungen dürfen an README/Docs angelehnt sein, aber für Einsteiger etwas vereinfacht werden.

---

## 7. Verbindung zu bestehenden Design-Dokumenten

- **Asset-Struktur:**  
  - Siehe `docs/design/asset_structure.md` – legt Pfade, Namen und Kategorien fest.
- **Icon-/Illustrations-Inventar:**  
  - Siehe `docs/design/icon_inventory.md`, `docs/design/illustration_inventory.md`.
- **Visual Asset Reuse:**  
  - Siehe `docs/website/visual_asset_reuse.md` – welche Assets App + Website gemeinsam nutzen.

setuphelfer.de folgt diesen Dokumenten; es werden keine parallelen, unkoordinierten Branding-Systeme aufgebaut.

---

## 8. Selbstprüfung Phase 4 – Branding

- **Mit PI-Installer visuell verbunden?**
  - Ja: gleiche Farb- und Iconwelt, Screenshots und Illustrationen werden wiederverwendet.
- **Keine neuen Marken/Produkte erfunden?**
  - Ja: Nur SetupHelfer (Plattform) und PI-Installer (Produkt) sind benannt.
- **Branding-Nutzung klar dokumentiert?**
  - Ja: Farbe, Icons, Tux/Pi-Einsatz und Tonfall sind beschrieben, ohne technische Umsetzung vorwegzunehmen.

