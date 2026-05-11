## Priorität C – Kosmetische & nachrangige Punkte (Backlog)

_Stand: März 2026 – Nur dokumentiert, nicht behoben._

Bewertungsskala:

- **Dringlichkeit**: niedrig / mittel (für spätere Runden)
- **Risiko bei Nichtbehebung**: gering (kein Laufzeitfehler, keine gravierende Fehlleitung)

---

### C‑01 – Uneinheitliche Primärbutton-Farben

- **Problem**:
  - Review-Dokumente (z. B. `ui_consistency_report.md`, `visual_ux_improvements.md`) nennen Stellen, an denen Primäraktionen unterschiedliche Farben verwenden (z. B. `bg-sky-600`, `bg-emerald-600`, `bg-purple-600` für ähnlich gewichtete Buttons).
- **Ort**:
  - `ControlCenter` (WLAN-Scan), `PeripheryScan`, einzelne Setup/Installations-Seiten.
- **Empfohlene spätere Maßnahme**:
  - Primäraktionen auf eine einheitliche Farbpalette normieren (wahrscheinlich „sky“ für globale Primärbuttons).
- **Dringlichkeit**: niedrig.  
- **Risiko bei Nichtbehebung**: gering; rein visuelle Inkonsistenz.

---

### C‑02 – Typografie-Feinheiten (Überschriften/Abstände)

- **Problem**:
  - In einigen Seiten (v. a. lange Dashboards und Wizards) sind Abstände zwischen Überschrift, Untertitel und Inhalt nicht durchgängig identisch (z. B. verschiedene `mb-*` Klassen).
- **Ort**:
  - `Dashboard`, `InstallationWizard`, `BackupRestore`, `SettingsPage`.
- **Empfohlene spätere Maßnahme**:
  - Gemeinsame Headline-Komponente oder Style-Guideline anwenden; Abstände und Schriftgrößen vereinheitlichen.
- **Dringlichkeit**: niedrig.  
- **Risiko bei Nichtbehebung**: gering; nur optisch.

---

### C‑03 – Restbestände älterer Begriffe in Neben-Texten

- **Problem**:
  - In Tooltips, Hinweisen und Fußnoten tauchen vereinzelt ältere Begriffe („Setup“, „Deploy“, „Debug“) auf, obwohl Hauptüberschriften weitgehend konsistent sind.
- **Ort**:
  - Hilfetexte in `SettingsPage`, `ControlCenter` (Performance/Display), vereinzelt in Doku-Passagen.
- **Empfohlene spätere Maßnahme**:
  - Bei Gelegenheit Textpassagen gegen `terminology_cleanup.md` prüfen und angleichen.
- **Dringlichkeit**: niedrig.  
- **Risiko bei Nichtbehebung**: gering; leichte kognitive Reibung, aber keine Fehlbedienung.

---

### C‑04 – Inkonsistente Icon-Größen im Detail

- **Problem**:
  - In einigen Karten/Listen werden Icons gelegentlich mit abweichenden Größen (z. B. 20px vs. 24px) verwendet, ohne dass dies funktional begründet ist.
- **Ort**:
  - Module-Kacheln im `Dashboard`, Status-Anzeigen in Detailkarten, bestimmte Periphery-Scan-Abschnitte.
- **Empfohlene spätere Maßnahme**:
  - Pro Komponententyp (Kachel, Inline-Icon, Badge) feste Standardgrößen definieren und anwenden.
- **Dringlichkeit**: niedrig.  
- **Risiko bei Nichtbehebung**: gering; visuelle Unruhe.

---

### C‑05 – Layout-Kleinigkeiten bei langen Texten

- **Problem**:
  - Längere Fehlermeldungen oder Hinweise brechen in einzelnen Karten nicht optimal um (z. B. sehr lange Sätze in Toasts oder Warnboxen).
- **Ort**:
  - Backend-Fehlerkarte im `Dashboard`, einzelne Warnhinweise in `BackupRestore` und `ControlCenter`.
- **Empfohlene spätere Maßnahme**:
  - Textlängen kürzen, Zeilenumbrüche/Max-Breite definieren oder in Bullet-Listen aufteilen.
- **Dringlichkeit**: niedrig.  
- **Risiko bei Nichtbehebung**: gering; beeinträchtigt nur Lesekomfort.

---

### Selbstprüfung Phase 3

- **Wurden C-Punkte nicht unnötig überarbeitet?**  
  - Ja. Es wurden keine UI-Änderungen durchgeführt, nur der Backlog beschrieben.

- **Wurden keine neuen Features eingebaut?**  
  - Ja. Alle Einträge sind rein dokumentarisch.

- **Wurde der Fokus auf Dokumentation beibehalten?**  
  - Ja. Die Datei dient ausschließlich als spätere To-do-Liste für kosmetische Arbeiten.

