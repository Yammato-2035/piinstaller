# Komponenten-Patterns – setuphelfer.de

_Ziel: Zentrale Website-Komponenten definieren, die das visuelle System konkret machen und für WordPress-Templates leicht umsetzbar sind._

---

## 1. Hero-Bereich

- **Einsatzorte:**
  - Home (`/`).
  - Optional auf wichtigen Unterseiten (z. B. Download, Über).

- **Bestandteile:**
  - Titel (Hauptbotschaft, z. B. „Dein Setup-Helfer für Raspberry Pi & Linux“).
  - Untertitel mit 1–2 Sätzen Erklärung.
  - Primärer CTA-Button (z. B. „Installer herunterladen“).
  - Sekundärer CTA (z. B. „Mehr erfahren“, „Projekte entdecken“).
  - Hero-Grafik:
    - Screenshot des PI-Installer-Dashboards oder Illustration (Pi + Tux).

- **Layout:**
  - Zwei-Spalten-Layout auf Desktop (Text + Grafik).
  - Einfacher Stack auf Mobilgeräten.

---

## 2. Feature-Karten

- **Einsatzorte:**
  - Home („Vorteile“, „Was macht der PI-Installer?“).
  - „Über SetupHelfer“.

- **Inhalt:**
  - Icon (z. B. Navigation-/Status-Icon).
  - Kurzer Titel (z. B. „Sichere Einrichtung“).
  - 2–3 Zeilen Beschreibung.

- **Gestaltung:**
  - Kleine Karte im `bg-elevated`-Stil.
  - Dezent animierter Hover.

---

## 3. Projektkarten

- **Einsatzorte:**
  - `/projekte/` und Kategorieseiten.

- **Inhalt:**
  - Projekt-Titel.
  - Kurzbeschreibung.
  - Difficulty-Badge.
  - Risk-Badge.
  - Kategorie-/Hardware-Infos (kurz).
  - Optional ein kleines Projekt-Icon/Illustration.

- **Aktion:**
  - „Projekt ansehen“ (Link zur Projektdetailseite).

---

## 4. Tutorialkarten

- **Einsatzorte:**
  - `/tutorials/` und Kategorieseiten.

- **Inhalt:**
  - Titel.
  - Kurzbeschreibung.
  - Difficulty-Badge.
  - Geschätzte Dauer.
  - Kategorie(n).

- **Aktion:**
  - „Tutorial ansehen“.

---

## 5. Community-Karten

- **Einsatzorte:**
  - `/community/`.

- **Inhalt:**
  - Bereiche wie:
    - „Hilfe & Support“.
    - „Projekte teilen“.
    - „Ankündigungen“.
  - Icon (z. B. Community-/Help-bezogene Icons).
  - Kurzbeschreibung, was Nutzer dort tun können.

- **Aktion:**
  - Link zum entsprechenden Forum-Bereich oder Forenübersicht.

---

## 6. Download-Boxen

- **Einsatzorte:**
  - `/download/`.

- **Varianten:**
  - **Einsteiger-Box:**
    - Klarer Titel („Empfohlene Installation für Einsteiger“).
    - Kurze Erklärung des Weges.
    - Button „Download starten“ (z. B. Link auf .deb oder Schritt für Schritt).
  - **Fortgeschrittenen-Boxen:**
    - z. B. „Skriptbasierte Installation“, „Docker-Test“.
    - Jeweils mit kurzer Erklärung und Link auf GitHub/Docs.

---

## 7. Status- / Difficulty-Badges

- **Verwendung:**
  - Auf Projektkarten, Projektdetailseiten, Tutorials.

- **Typen:**
  - Difficulty: Anfänger | Fortgeschritten | Experte.
  - Risk: niedrig | mittel | hoch.

- **Gestaltung:**
  - Kleine, farbige Kapseln mit Text.
  - Farben angelehnt an visuelles System (Status-/Risk-Farben).

---

## 8. Hinweisboxen

- **Varianten:**
  - Info (neutral).
  - Warnung.
  - Sicherheit/Kritisch.

- **Einsatz:**
  - In Tutorials und Doku-Artikeln.
  - Inhalt z. B.:
    - „Tipp: So kannst du…“
    - „Achtung: Mache vorher ein Backup.“
    - „Sicherheits-Hinweis: Bitte nicht direkt aus dem Internet erreichbar machen.“

---

## 9. Tux-Hinweis-Komponenten

- **Einsatzorte:**
  - Einsteiger-Tutorials.
  - Linux-Erklärseiten in der Doku.

- **Inhalt:**
  - Kleine Illustration mit Tux (optional Pi).
  - Kurzer erklärender Textblock:
    - „So funktioniert das unter Linux…“
    - „Wenn du neu bei Linux bist, merke dir: …“

---

## 10. Layout-Patterns

- **Zweispaltige Sektionen:**
  - Links Text, rechts Bild/Illustration (oder umgekehrt).
  - Einsatz auf Home, Über, Projektdetailseiten.

- **Listen-/Rasteransichten:**
  - Raster mit Karten (Projekte/Tutorials).
  - Filterleiste darüber (UI-Sicht, nicht als technische Funktion hier beschrieben).

---

## 11. Selbstprüfung Phase 4 – Komponenten-Patterns

- **Visueller Stil konsistent mit dem Installer?**
  - Ja: Karten, Badges, Icons und Farbwelt sind klar an die App angelehnt.
- **Wiederverwendbare Komponenten klar definiert?**
  - Ja: Hero, Feature-Karten, Projekt-/Tutorial-/Community-Karten, Download-Boxen, Badges, Hinweisboxen, Tux-Hinweise.
- **Keine unnötige Komplexität?**
  - Ja: Nur Komponenten, die für die geforderte Struktur nötig sind; keine zusätzlichen UI-Spielereien.

