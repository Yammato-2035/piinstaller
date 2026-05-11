# Abschlussbericht: Status visueller Assets – PI-Installer

_Stand: März 2026 – Systematische Dokumentation der grafischen Assets: vorhanden, fehlend, Konsistenz, Empfehlungen._

---

## 1. Kontext und Vorgabe

- **Keine neuen Funktionen**, **keine UI-Umbauten**, **keine neuen Komponenten** – ausschließlich **Dokumentation und Struktur** für Assets.
- **Ziel:** Vollständige Übersicht Icons, Dokumentation fehlender Grafiken, gemeinsame Assetstruktur für **Installer**, **Dokumentation** und **Website setuphelfer.de**.

---

## 2. Vorhandene Assets

### 2.1 Icons (vollständig inventarisiert)

| Bereich | Anzahl | Pfad | Dokumentation |
|--------|--------|------|----------------|
| Navigation | 9 | `frontend/public/assets/icons/navigation/` | `docs/design/icon_inventory.md` |
| Status | 8 | `frontend/public/assets/icons/status/` | ebd. |
| Devices | 9 | `frontend/public/assets/icons/devices/` | ebd. |
| Process | 7 | `frontend/public/assets/icons/process/` | ebd. |
| Diagnostic | 5 | `frontend/public/assets/icons/diagnostic/` | ebd. |
| **Summe** | **38 SVG** | `frontend/public/assets/icons/` | |

- **Nutzung:** Über Komponente `AppIcon` (`frontend/src/components/AppIcon.tsx`) mit Kategorien und optionaler Status-Einfärbung (CSS-Filter).
- **Zwei ungenutzte Dateien im Repo:** `status_update.svg`, `device_network.svg` (nicht in AppIcon-Maps referenziert).

### 2.2 Illustrationen, Statusgrafiken, Prozessdiagramme

- **Vorhanden:** Keine. Es existieren keine Dateien in `assets/illustrations/` oder `assets/diagrams/`.
- **Screenshots:** In Doku und UI referenziert (z. B. `screenshot-dashboard.png`, `screenshot-wizard.png` …); **Dateien nicht im Repo** – nur Ordner `frontend/public/docs/screenshots/` mit README.

---

## 3. Fehlende Assets (dokumentierte Liste)

Vollständige Auflistung in **`docs/design/missing_graphics.md`**. Kurzüberblick:

| Kategorie | Fehlende Grafiken (Stichworte) |
|-----------|-------------------------------|
| **Onboarding** | welcome, system check, experience selection, secure setup, backup setup, discover projects |
| **Projects** | media server, NAS, smart home, music box, photo frame, retro gaming, learning environment, system monitor |
| **Setup-Diagramme** | setup flow, backup flow, install process, network connection, device detection |
| **Statusgrafiken** | system ok, system warning, system problem, maintenance, check running |
| **Empty States** | no projects, no backups, no devices, no logs |
| **Community** | community, share projects, help |
| **Risk-System** | safe, warning, critical |

---

## 4. Konsistenz des Icon-Systems

- **Stärken:**
  - Einheitliche Kategorien (navigation, status, devices, process, diagnostic) und klare Dateibenennung.
  - Zentrale Nutzung über `AppIcon`; Statusfarben über CSS-Filter konsistent (ok, warning, error, info, muted).
  - Alle Icons sind SVG und websitefähig (keine App-exklusiven Pfade im Asset).

- **Schwächen / offene Punkte:**
  - **Doppelsystem AppIcon + Lucide:** In vielen Stellen werden parallel Lucide-Icons (`lucide-react`) genutzt. Visuell nicht vollständig vereinheitlicht; bewusst dokumentiert, kein Refactoring in dieser Phase.
  - **Zwei Icons ohne AppIcon-Anbindung:** `status_update.svg`, `device_network.svg` – entweder in AppIcon aufnehmen oder als „reserviert“ führen.
  - **Mehrfachnutzung einer Datei:** Mehrere logische Begriffe teilen sich ein SVG (z. B. backup/storage, help/documentation, diagnose/periphery-scan/monitoring). Das ist gewollt, sollte bei Erweiterungen beachtet werden.

- **Fazit:** Das Icon-System ist **strukturell konsistent** und für Installer und Website wiederverwendbar; optische Vereinheitlichung mit Lucide und Anbindung der beiden „freien“ Icons sind optionale Folgeaufgaben.

---

## 5. Empfehlungen für spätere Grafikproduktion

1. **Priorität 1 – Onboarding & Empty States**  
   Zuerst: welcome, system check, experience selection, secure setup, backup setup, discover projects; no projects, no backups, no devices, no logs. Diese verbessern First-Run und leere Listen in App und eignen sich für setuphelfer.de („Erste Schritte“, Doku).

2. **Priorität 2 – Projekte & Status**  
   Projekt-Illustrationen (media server, NAS, smart home, …) und größere Statusgrafiken (system ok, warning, problem, maintenance, check running) für einheitliches Erscheinungsbild und bessere Erklärbarkeit.

3. **Priorität 3 – Diagramme & Risiko**  
   Setup-/Backup-/Install-/Netzwerk-/Geräte-Diagramme; Risk-Illustrationen (safe, warning, critical) für Doku und ggf. RiskLevelBadge/RiskWarningCard.

4. **Technik**  
   - Benennung und Ordnerstruktur wie in **`docs/design/asset_structure.md`** (Dateibenennung, SVG-Regeln, Farbnutzung).
   - Stil und Farben an **`docs/design/graphics_system.md`** und App-Farben (Sky, Statusfarben) anpassen.
   - SVG möglichst mit `currentColor`/Variablen, damit Theme und Website-Nutzung einfach bleiben.

5. **Screenshots**  
   Referenzierte Screenshots (siehe `docs/design/illustration_inventory.md`) einmalig erstellen und in einer gemeinsamen Ablage ablegen (z. B. `frontend/public/docs/screenshots/` oder `assets/screenshots/`), damit Doku und setuphelfer.de dieselben Dateien nutzen können.

6. **Website**  
   Alle neuen Illustrationen und Diagramme von vornherein **websitefähig** gestalten (keine App-spezifischen Pfade in SVG/PNG); Wiederverwendung wie in **`docs/website/visual_asset_reuse.md`** beschrieben.

---

## 6. Erstellte Dokumentation (Übersicht)

| Dokument | Inhalt |
|----------|--------|
| **docs/design/icon_inventory.md** | Vorhandene Icons, Kategorien, Nutzung im Code, mögliche Duplikate/Mehrfachnutzung |
| **docs/design/illustration_inventory.md** | Vorhandene Illustrationen/Statusgrafiken/Diagramme; Screenshot-Referenzen; Ergebnis: nur Icons + referenzierte Screenshots |
| **docs/design/missing_graphics.md** | Liste fehlender Grafiken (Onboarding, Projects, Setup, Status, Empty States, Community, Risk) |
| **docs/design/asset_structure.md** | Einheitliche Assetstruktur (icons, illustrations, diagrams), Dateibenennung, SVG-Regeln, Farbnutzung, Website-Wiederverwendung |
| **docs/website/visual_asset_reuse.md** | Welche Assets auf setuphelfer.de nutzbar sind; welche Illustrationen Installer + Website gemeinsam nutzen können |
| **docs/review/visual_asset_status.md** | Dieser Abschlussbericht |

---

## 7. Selbstprüfung (alle Phasen)

- **Keine neuen Funktionen entwickelt?** – Ja.
- **Keine UI umgebaut?** – Ja.
- **Nur Dokumentation und Struktur erstellt?** – Ja.
- **Keine unnötigen Refactorings?** – Ja.
- **Assetstruktur websitefähig dokumentiert?** – Ja.

---

_Dokumentation abgeschlossen. Nächster Schritt bei Bedarf: Grafikproduktion anhand der Prioritäten und der in `asset_structure.md` und `graphics_system.md` beschriebenen Regeln._
