## Priorität B – Konsistenzfehler (Icons, Begriffe, UI-System)

_Stand: März 2026 – Fokus auf Dokumentation und Struktur, keine funktionalen Änderungen._

---

### B‑01 – Icon-System: AppIcon vs. Lucide-Icons (gemischt)

- **Problem**:
  - Die App verwendet zwei parallele Icon-Systeme:
    - `AppIcon` (SVG-Icons aus `/assets/icons/...` gemäß Design-Doku).
    - Lucide-Icons (`lucide-react`) für viele Inline-Symbole.
  - Dies führt zu uneinheitlichem Stil, ist aber funktional unkritisch.
- **Betroffene Bereiche**:
  - `Dashboard`, `BackupRestore`, `ControlCenter`, `SettingsPage`, diverse Setup-Seiten.
- **Risiko**:
  - Visuelle Inkonsistenz, erschwerte Pflege bei weiteren UI-Änderungen.
- **Status**:
  - In `docs/design/asset_inventory.md` und `docs/design/shared_icon_and_graphics_plan.md` dokumentiert.
  - Kein Code angepasst.
- **Empfohlene Maßnahme (später)**:
  - Klare Regel definieren, welche Bereiche AppIcon-basiert und welche bewusst Lucide-basiert sind.

---

### B‑02 – Asset-Struktur: Quell- vs. Build-Icons

- **Problem**:
  - Design-Dokumente gehen von `frontend/public/assets/icons/...` als Quellablage aus.
  - Im Repo sind vor allem generierte Icons unter `frontend/dist/assets/icons/...` sichtbar.
  - Unklar, wo die „Master“-SVGs für künftige Website-/CI-Nutzung liegen sollen.
- **Risiko**:
  - Doppelpflege oder Verlust von Ursprungsgrafiken.
- **Status**:
  - In `asset_inventory.md` und `shared_icon_and_graphics_plan.md` beschrieben.
  - Keine Umstrukturierung vorgenommen.
- **Empfohlene Maßnahme (später)**:
  - Eindeutige Quelle definieren und dokumentieren; Build-Ziele daraus ableiten.

---

### B‑03 – Illustrationen / Empty States (nur konzipiert)

- **Problem**:
  - `graphics_system.md` beschreibt Illustrationen für leere Zustände (kein Gerät, keine Module, kein Netzwerk, keine Fehler).
  - Entsprechende Dateien sind im Repo nicht sichtbar.
- **Risiko**:
  - Konzeptlücke, aber kein unmittelbarer Fehler – leere Zustände werden derzeit textbasiert behandelt.
- **Status**:
  - Dokumentiert in `asset_inventory.md` und `shared_icon_and_graphics_plan.md`.
- **Empfohlene Maßnahme (später)**:
  - Separates Asset-Projekt aufsetzen, Illustrationen erstellen und in `frontend/public/assets/illustrations/empty_states/` ablegen.

---

### B‑04 – Terminologie-Mischung (Setup/Deploy/Debug vs. Installation/Einstellungen/Diagnose)

- **Problem**:
  - UI-Komponenten und Doku verwenden teils englische/technische Begriffe („Setup“, „Deploy“, „Debug“, „Settings“) statt der in `ux_guidelines.md` definierten deutschen Begriffe.
  - Besonders sichtbar in Dateinamen (`*Setup.tsx`) und älteren Doku-Dateien.
- **Risiko**:
  - Erhöhte Einstiegshürde für Einsteiger, inkonsistente Kommunikation.
- **Status**:
  - Systematisch in `docs/design/terminology_cleanup.md` erfasst.
  - Keine Texte geändert.
- **Empfohlene Maßnahme (später)**:
  - Sichtbare UI-Texte schrittweise an die Guidelines angleichen, Dateinamen aus Stabilitätsgründen zunächst belassen.

---

### B‑05 – Screenshots-Pfade in README & Docs

- **Problem**:
  - README und einige Doku-Dateien referenzieren `docs/screenshots/screenshot-*.png`, der Ordner ist laut System-Audit nicht im Repo enthalten.
  - Dies betrifft vor allem die Darstellung von GUI-Screenshots.
- **Risiko**:
  - Fehlende Bilder, aber kein Laufzeitfehler.
- **Status**:
  - Als Dokumentationsbruch in `documentation_breaks.md` und in den Design-Dokumenten (Assets/Graphics) vermerkt.
  - In dieser Phase **nicht** entfernt, um die Stelle sichtbar zu halten.
- **Empfohlene Maßnahme (später)**:
  - Entweder Screenshots zentral in einem Assets-Bereich ablegen oder README auf eine externe Quelle (z. B. Website) verweisen.

---

### Selbstprüfung Phase 2 (Priorität B)

- **Wurde nichts funktional erweitert?**  
  - Ja. Es wurden ausschließlich neue Dokumente und Pläne angelegt.

- **Wurde primär dokumentiert?**  
  - Ja. Asset-Inventar, Icon/Grafik-Plan und Terminologie-Backlog sind rein beschreibend.

- **Wurden Icons/Grafiken nur strukturell vorbereitet?**  
  - Ja. Es gibt keine neuen Icons, keine Map-Änderungen im Code; nur Dokumentation der Zielstruktur.

- **Ist spätere Website-Nutzung berücksichtigt, ohne Website zu bauen?**  
  - Ja. Die Pläne sind auf Wiederverwendbarkeit ausgelegt, aber nicht implementiert.

