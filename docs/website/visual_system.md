# Visuelles System – setuphelfer.de

_Ziel: Ein konsistentes, wiederverwendbares Designsystem für setuphelfer.de, das klar an den PI-Installer angelehnt ist (gleiche Designfamilie), ohne neue UI-Funktionalität zu erfinden._

---

## 1. Designprinzipien

- **Anfängerfreundlich:**
  - Klare Hierarchien, viel Weißraum, verständliche Sprache.
  - Komplexe technische Details erst in der Doku, nicht auf der Startseite.
- **Familienzugehörigkeit zum PI-Installer:**
  - Gleiche Grundfarbwelt (Dark + Sky-Blue-Akzente).
  - Wiederverwendung der Icon-Sets und Screenshots.
  - Ähnliche Karten- und Badge-Stile.
- **Ruhig, nicht überladen:**
  - Wenige, klar definierte Komponenten.
  - Keine übertriebenen Animationen oder „Marketing-Gimmicks“.

---

## 2. Farbpalette

Angelehnt an die in den Design-Dokumenten beschriebenen Farben (Sky-Blau + Statusfarben):

- **Grundfarben:**
  - `bg-dark` – Dunkler Hintergrund (z. B. sehr dunkles Grau/Blau, wie im Installer verwendet).
  - `bg-elevated` – leicht hellerer Hintergrund für Karten und Sektionen (Glasmorphism-Effekt möglich).
  - `fg-primary` – Helle Schrift (weiß/helles Grau).
  - `accent-sky` – Sky-Blau (z. B. `#0ea5e9` / `#0284c7`) für primäre Hervorhebungen (Links, Buttons).

- **Statusfarben (Risiko/Status):**
  - `status-ok` – Grün (für „alles in Ordnung“).
  - `status-warning` – Gelb/Orange (für Vorsicht/„bitte lesen“).
  - `status-error` – Rot (für Fehler/Kritisches).
  - `status-info` – Blau (für neutrale Hinweise).
  - `status-muted` – Gedämpftes Grau (deaktiviert/sekundär).

Diese Farben sollten mit den bereits dokumentierten Statusfiltern/Badges in der App abgestimmt sein (siehe Icon-/Graphics-Dokumente).

---

## 3. Typografie

Konzeptuell (konkrete Webfont-Auswahl später im Theme):

- **Grundschrift:**
  - Moderne, gut lesbare Sans-Serif-Schrift (ähnlich oder identisch zur App-Typografie).
- **Hierarchie:**
  - `H1` – Hauptüberschriften (z. B. Hero-Titel, Seitentitel).
  - `H2` – Sektionstitel (z. B. „Vorteile“, „Projekte“, „Tutorials“).
  - `H3` – Untersektionen (z. B. Kartenüberschriften, Schrittüberschriften).
  - Fließtext – für Beschreibungen und Anleitungen.
- **Lesbarkeit:**
  - Ausreichende Zeilenhöhe.
  - Kontrast gemäß WCAG (insbesondere auf dunklem Hintergrund).

---

## 4. Kartenstil

Wird für Projekte, Tutorials, Doku-Teaser und Community-Karten genutzt:

- **Layout:**
  - Abgerundete Ecken, dezente Schatten oder Glasmorphism-Effekt (wie im Installer beschrieben).
  - Hintergrund `bg-elevated`, Text `fg-primary`.
- **Inhalte:**
  - Icon oder kleines Bild oben/links (SVG aus Icon-Set).
  - Titel, Kurzbeschreibung.
  - Metadaten (Badges für Difficulty/Risk/Kategorien).
- **Verhalten:**
  - Dezent hervorgehobener Hover (leichte Skalierung/Hintergrundaufhellung).

---

## 5. Buttons

- **Primäre Buttons:**
  - Hintergrund `accent-sky`, Text hell.
  - Verwendung:
    - Haupt-CTAs wie „Installer herunterladen“, „Projekt ansehen“, „Zur Community“.
- **Sekundäre Buttons/Links:**
  - Rahmen oder Text in `accent-sky` auf transparentem/abgesetztem Hintergrund.
  - Verwendung:
    - „Mehr erfahren“, „Alle Tutorials anzeigen“.

Buttons sollen optisch zur App passen, aber für Web (WordPress-Theme) einfach nachbaubar sein.

---

## 6. Icons & Illustrationen

- **Icons:**
  - Nutzung des bestehenden Icon-Sets:
    - `navigation`, `status`, `devices`, `process`, `diagnostic` (siehe `docs/design/icon_inventory.md`).
  - Einsatz im Web:
    - Hauptnavigation (z. B. Dashboard/Home, Installation, Hilfe).
    - Karten (z. B. Status, Geräte, Prozesse).

- **Illustrationen:**
  - Onboarding-/Projekt-/Status-/Risk-Illustrationen wie in `missing_graphics.md` beschrieben.
  - Gemeinsame Nutzung:
    - Installer (z. B. Onboarding, Empty States).
    - Website (z. B. Landingpage-Sektionen, Doku).

- **Screenshots:**
  - Einheitliche Ablage und Wiederverwendung (siehe Asset-Struktur).
  - Verwendung vor allem in:
    - Home (Beispiel-Screenshots).
    - Download (Oberflächenvorschau).
    - Tutorials/Doku (konkrete Schritte).

---

## 7. Maskottchen / Tux / Raspberry-Pi-Ästhetik

- **Einsatz:**
  - Dezent, unterstützend, nicht dominierend.
  - Beispiele:
    - Tux-Illustration in „Linux-Einstieg“-Sektionen.
    - Raspberry-Pi-Silhouette in Hero-Grafik oder Projektübersichten.
- **Stil:**
  - Gleiche Farbpalette wie restliches Design (kein Stilbruch).
  - Freundlich, aber nicht verspielt in einem Maße, das Seriosität mindert.

---

## 8. Status- und Difficulty-Labels

- **Difficulty-Badges (Schwierigkeit):**
  - `Anfänger` – z. B. Badge mit heller, beruhigender Farbe.
  - `Fortgeschritten` – mittlere Intensität.
  - `Experte` – deutlicher, aber nicht aggressiver Ton.

- **Risk-Badges (Risiko):**
  - `niedrig` – angelehnt an `status-ok`.
  - `mittel` – angelehnt an `status-warning`.
  - `hoch` – angelehnt an `status-error`.

Badges werden sowohl auf Projekt- als auch auf Tutorialseiten eingesetzt und sind mit dem dokumentierten Risk/Difficulty-System kompatibel.

---

## 9. Hinweisboxen

Standardisierte Boxen zur Markierung von Hinweisen in Tutorials und Doku:

- **Typen:**
  - Info (neutral, z. B. blau).
  - Warnung (z. B. gelb/orange).
  - Sicherheit/Kritisch (rot, für wichtige Sicherheits-Hinweise).

- **Einsatz:**
  - In Tutorials (z. B. „Achtung: Backup vor Änderungen machen“).
  - In Doku (z. B. „Nicht direkt im Internet freigeben, besser VPN nutzen“).

---

## 10. Tux-Hinweis-Komponenten

Spezielle, leicht wiedererkennbare Hinweise, die sich an Linux-Einsteiger richten:

- **Beispiel-Komponente:**
  - Kleine Illustration (Tux oder Tux+Pi).
  - Kurzer Textblock mit:
    - Einsteiger-Tipp.
    - „So funktioniert das unter Linux…“-Erklärung.
- **Verwendung:**
  - Auf Einsteigerseiten (Home, Tutorials für grundlegende Linux-Schritte).
  - In Doku-Bereichen, in denen typische Linux-Fragen auftauchen.

---

## 11. Selbstprüfung Phase 4 – Visuelles System

- **Visueller Stil konsistent mit dem Installer?**
  - Ja: Dark + Sky-Blue, vorhandene Icons, Screenshots und geplante Illustrationen werden wiederverwendet.
- **Wiederverwendbare Komponenten definiert?**
  - Ja: Karten, Buttons, Badges, Hinweisboxen, Tux-Hinweise sind als Bausteine beschrieben.
- **Nichts unnötig aufgeblasen?**
  - Ja: Fokus liegt auf wenigen, klaren Komponenten statt auf komplexen Designsystemen oder Spezialeffekten.

