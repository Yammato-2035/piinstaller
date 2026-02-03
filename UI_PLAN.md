# UI-Plan: Bessere Oberfläche für PI-Installer

Kurzfristiger, umsetzbarer Plan für eine spürbar bessere UI. Baut auf [UI_IMPROVEMENTS.md](./UI_IMPROVEMENTS.md) auf und priorisiert nach Aufwand/Nutzen.

---

## 1. Aktueller Stand (Ist-Zustand)

| Bereich | Status | Anmerkung |
|--------|--------|-----------|
| **Theme** | ✅ | Light/Dark/System, in Sidebar + localStorage |
| **Glasmorphism** | ✅ | `.card`, `.glass` in App.css, teilweise genutzt |
| **Charts** | ✅ | Recharts im Dashboard (CPU, RAM, Temperatur, Disk) |
| **Animationen** | ✅ | Framer Motion (StatCards, Einblendungen), fadeIn in App.css |
| **Skeletons** | ⚠️ | Klassen in App.css (`.skeleton`, `.skeleton-text`), nicht überall genutzt |
| **Seitentransition** | ⚠️ | `.page-transition` vorhanden, nicht in App.tsx eingebunden |
| **Design-System** | ⚠️ | Tailwind + eigene Klassen, keine zentralen Design-Tokens |
| **Navigation** | ⚠️ | Sidebar gut, keine Breadcrumbs, keine globale Suche |
| **Mobile** | ⚠️ | Responsive, aber keine Bottom-Nav, Touch-Ziele nicht geprüft |
| **Accessibility** | ⚠️ | Keine systematischen ARIA-Labels / Fokus-Indikatoren |

**Tech-Stack:** React 18, TypeScript, Vite, Tailwind, Lucide, Recharts, Framer Motion, react-hot-toast, Zustand.

---

## 2. Ziele der UI-Verbesserung

- **Weniger kognitiver Aufwand:** Klare Hierarchie, erkennbare Aktionen, konsistente Muster.
- **Moderner Look:** Glasmorphism und Mikro-Interaktionen einheitlich nutzen; keine neuen großen Bibliotheken.
- **Bessere Wahrnehmung von Zustand:** Loading = Skeleton statt nur Spinner; Status klar (Erfolg/Warnung/Fehler).
- **Grundlagen für Skalierung:** Design-Tokens und wiederverwendbare Komponenten vorbereiten.

---

## 3. Phase 1: Quick Wins (1–2 Tage)

Sofort sichtbare Verbesserungen mit wenig Risiko.

### 3.1 Seitentransition aktivieren

- **Wo:** `frontend/src/App.tsx`
- **Was:** Den Content-Container mit `className="page-transition"` (oder Framer `AnimatePresence` + `motion.div`) umhüllen, damit Seitenwechsel einheitlich eingeblendet werden.
- **Akzeptanz:** Jeder Seitenwechsel hat eine kurze, sanfte Einblendung.

### 3.2 Loading-Skeletons konsequent nutzen

- **Wo:** Seiten mit Datenabfragen (z. B. Dashboard, SecuritySetup, UserManagement, MonitoringDashboard).
- **Was:** Beim ersten Laden statt Spinner oder leerem Bereich Skeleton-Blöcke anzeigen (mit vorhandenen `.skeleton`-Klassen oder kleinen Skeleton-Komponenten).
- **Akzeptanz:** Keine „leeren“ weißen Flächen beim Laden; Nutzer erkennt sofort „wird geladen“.

### 3.3 Einheitliche Card-Nutzung

- **Wo:** Alle Seiten mit Karten (Dashboard, Wizard, Setup-Seiten).
- **Was:** Überall die bestehende `.card`-Klasse (Glasmorphism) nutzen; wo nötig eine leichte Variante z. B. `.card-subtle` für weniger hervorgehobene Blöcke.
- **Akzeptanz:** Optisch einheitliche Karten; Hover-Verhalten wie in App.css definiert.

### 3.4 Status-Icons und Badges vereinheitlichen

- **Wo:** Überall, wo Status angezeigt wird (z. B. Dashboard, Monitoring, Backup, Dienste).
- **Was:** Einheitliche Farben (z. B. success/warning/danger aus Tailwind) und gleiche Icon-Größen; wo sinnvoll `.status-icon.active` für „läuft“ nutzen.
- **Akzeptanz:** Status auf einen Blick erkennbar; gleiche Semantik auf allen Seiten.

### 3.5 Schrift und Kontrast prüfen

- **Wo:** `index.css`, `index.html` (Font: Source Sans 3 ist bereits verlinkt).
- **Was:** Sicherstellen, dass `font-family` konsistent (z. B. Source Sans 3) und Kontraste für Text in Light/Dark ausreichend sind (WCAG AA).
- **Akzeptanz:** Lesbarkeit in beiden Themes gut; eine klare Typo-Hierarchie (H1, H2, Body).

---

## 4. Phase 2: Dashboard & Orientierung (2–3 Tage)

### 4.1 Dashboard-Verfeinerung

- **Was:**  
  - Kurze Zusammenfassung „System Health“ (z. B. grün/gelb/rot) oben.  
  - Quick-Actions (z. B. „Sicherheit prüfen“, „Backup starten“) als deutlich klickbare Buttons.  
  - Optional: ein kleines „Letzte Aktionen“-Feed, falls Backend-Log vorhanden.
- **Akzeptanz:** Dashboard dient als klarer Einstieg und Wegweiser zu den wichtigsten Aktionen.

### 4.2 Breadcrumbs

- **Wo:** Oberhalb des Hauptinhalts (in `App.tsx` oder pro Seite).
- **Was:** Pfad anzeigen, z. B. „Dashboard → Sicherheit“. Route/`currentPage` auf Breadcrumb-Items mappen.
- **Akzeptanz:** Nutzer sieht immer „wo bin ich“ und kann eine Ebene zurück.

### 4.3 Bessere leere Zustände

- **Wo:** Listen (Benutzer, Module, Backups etc.).
- **Was:** Wenn keine Daten: kurzer Text + Icon + optional eine konkrete Aktion (z. B. „Ersten Benutzer anlegen“).
- **Akzeptanz:** Keine leeren weißen Listen ohne Erklärung.

---

## 5. Phase 3: UX & Feedback (2–3 Tage)

### 5.1 Tooltips für wichtige Aktionen

- **Wo:** Buttons und Links mit nicht selbsterklärendem Label (z. B. Assistent, Peripherie-Scan).
- **Was:** `title` oder eine kleine Tooltip-Komponente (z. B. nur mit CSS oder minimaler Lib); kurzer Hilfetext.
- **Akzeptanz:** Unklare Begriffe sind beim Hover/Focus erklärt.

### 5.2 Notification-/Toast-Verhalten vereinheitlichen

- **Wo:** Alle API-Aufrufe, die Erfolg/Fehler melden.
- **Was:** Einheitliche Nutzung von react-hot-toast (Erfolg grün, Fehler rot, Info neutral); bei längeren Aktionen „wird ausgeführt“ + danach „erledigt“.
- **Akzeptanz:** Klares, konsistentes Feedback für jede Aktion.

### 5.3 Formulare: Validierung und Fokus

- **Wo:** Alle Formulare (Benutzer, Wizard, Einstellungen).
- **Was:** Echtzeit-Validierung wo sinnvoll; nach Submit Fehler unter dem Feld anzeigen; Fokus auf erstes Fehlerfeld setzen; sichtbare Fokus-Ringe (z. B. `ring-2 ring-sky-500`).
- **Akzeptanz:** Weniger Rätselraten; bessere Tastatur-Nutzung.

---

## 6. Phase 4: Design-System & Wartbarkeit (3–5 Tage, optional)

### 6.1 Design-Tokens in Tailwind

- **Wo:** `tailwind.config.js`, ggf. `index.css` (CSS-Variablen).
- **Was:** Zentrale Werte für Farben (primary, success, warning, danger), Abstände (z. B. `spacing.page`), Radii, Schatten; in Tailwind `theme.extend` abbilden.
- **Akzeptanz:** Neue Komponenten nutzen dieselben Werte; Theme-Wechsel bleibt konsistent.

### 6.2 Kleine Komponenten-Bibliothek

- **Wo:** z. B. `frontend/src/components/ui/` (Button, Card, Badge, Skeleton, Alert).
- **Was:** Wiederverwendbare Basis-Komponenten, die die Tokens und bestehenden Klassen nutzen; keine neue UI-Bibliothek nötig.
- **Akzeptanz:** Neue Seiten bauen sich aus wenigen, einheitlichen Bausteinen zusammen.

### 6.3 Accessibility-Check

- **Was:**  
  - Wichtige Buttons/Links mit `aria-label` wo das Label fehlt.  
  - Überschriften-Hierarchie (ein H1 pro Seite).  
  - Fokus sichtbar und logisch (Tab-Reihenfolge).  
- **Akzeptanz:** Bessere Nutzung mit Tastatur und Screenreader; Grundlage für spätere Zertifizierung.

---

## 7. Priorisierung (Übersicht)

| Priorität | Inhalt | Aufwand |
|-----------|--------|--------|
| **P0** | Phase 1 (Quick Wins) | 1–2 Tage |
| **P1** | Phase 2 (Dashboard, Breadcrumbs, leere Zustände) | 2–3 Tage |
| **P2** | Phase 3 (Tooltips, Toasts, Formulare) | 2–3 Tage |
| **P3** | Phase 4 (Tokens, Komponenten, A11y) | 3–5 Tage |

---

## 8. Nächste Schritte

1. **Phase 1 starten:** Seitentransition in `App.tsx` einbauen und Skeleton-Nutzung auf 2–3 zentralen Seiten prüfen.
2. **UI_IMPROVEMENTS.md** für detaillierte Ideen (Charts, PWA, Mehrsprachigkeit etc.) weiter nutzen; dieser Plan konzentriert sich auf die nächsten 1–2 Sprints.
3. Nach Phase 1 kurzes Review: Lesbarkeit, Konsistenz der Karten und Ladezustände; dann Phase 2 angehen.

---

*Stand: Februar 2026. Basiert auf ARCHITECTURE.md, UI_IMPROVEMENTS.md und aktuellem Frontend-Code.*
