# Panda Companion & Ampel – Ist-Stand und ToDo

## Ist-Stand (was parallel existiert)

| Baustein | Ort | Rolle |
|----------|-----|--------|
| **PandaHelper** | `components/PandaHelper.tsx` | Kleines Mascot-Icon (SVG unter `/assets/mascot/`), 6 Varianten, kein Status, blendet bei „Entwickler“ aus |
| **PandaCompanion** | `components/companions/` | Kachel mit Text + vertikaler CSS-Ampel, Modul-Typen |
| **Dashboard-Ampel** | `Dashboard.tsx` | Eigene Typen `TrafficLight` = red/yellow/green, `TrafficLightDot` + `AreaLightCard` (Tailwind), keine Wiederverwendung von `companions/TrafficLight` |
| **Mascot-SVGs** | `public/assets/mascot/` | `panda_base`, `panda_backup`, … (konsistentes Rahmen-Motiv) |
| **Alte PNG-Pfade** | `src/assets/pandas/*.png` | Waren Platzhalter; durch SVG-Mascots ersetzt (siehe `public/assets/mascot/companions/`) |

## Behoben in dieser Iteration

- Einheitliche **Companion-Grafiken** über `public/assets/mascot/` (bestehende `panda_*` + neue `companions/*.svg` im Stil von `panda_backup`); `companionAssets.ts` als zentrale URL-Map.
- **Ampelfarben** in `TrafficLight.tsx` an Dashboard (`TrafficLightDot` / Emerald–Amber–Red) angeglichen.
- **Kontraste** in `PandaCompanion.module.css` (dunkle Variante) und **Dashboard-H1** mit `drop-shadow`.
- **Dashboard**: ein integrierter Begleiter im Kurzaktionen-Block (kein doppeltes PandaHelper + zweites Panda mehr); Texte über i18n inkl. Ampel-Hinweis.
- **`PandaRail`**: gemeinsamer äußerer Rahmen; **`PandaCompanion` `frame={false}`** vermeidet doppelte Kacheln (Dashboard, Backup, Peripherie-Scan).

## Zwischenstand (weitere Umsetzung)

- **`StatusDots.tsx`**: `LampDot` + `LampAreaCard` + `LampTriState` – Dashboard-Systemstatus nutzt diese Bausteine (keine Duplikate mehr in `Dashboard.tsx`).
- **PandaRail + PandaCompanion** auf: **SecuritySetup**, **ControlCenter**, **InstallationWizard**, **WebServerSetup**, **DevelopmentEnv** (Docker-Motiv), **NASSetup** (Cloud-Motiv), **HomeAutomationSetup**, **BackupRestore**, **PeripheryScan**, **Dashboard** (Kurzaktionen).
- **ControlCenter**: Bluetooth-State ergänzt; WLAN-Status beim Mount.
- **Sidebar**: ungenutzter `PandaHelper`-Import entfernt; **`PandaHelper`**-Variante `base` nutzt wie der Start-Begleiter `/assets/mascot/companions/start.svg` (für künftige Wiederverwendung konsistent).

## Offene ToDos (nächste Schritte)

1. **Ampel vertikal vs. Punkte**  
   - Optional: `TrafficLight` (vertikal) und `LampDot` (Punkte) visuell oder per Story dokumentieren; bei Bedarf dritte Variante „horizontale drei Punkte“ nur für kompakte Zeilen.

2. **PandaHelper**  
   - Komponente bleibt für kleine Icons; bei Bedarf weitere Varianten auf Companion-SVGs umstellen.

3. **Panda-Bereich pro Seite**  
   - Optional noch: **MusicBox**, **Kino/Streaming**, **Mailserver**, **Backup-Tab rein Cloud** – wenn dort ein eigener Einstiegsblock gewünscht ist.

4. **Illustrationen verfeinern**  
   - Companion-SVGs tragen nur kleine Badges; optional später echte Motiv-Varianten vom Designer (weiterhin: Panda = Modul, Ampel = Status getrennt).

5. **Barrierefreiheit**  
   - Live-Region oder `aria-live` wenn sich `status` dynamisch ändert; Fokus-Reihenfolge in eingeklappten `<details>` prüfen.

6. **Theming**  
   - Optional CSS-Variablen für Ampel/Panda-Rand, damit Light-Mode-Seiten identisch wirken.

## Designregeln (Referenz)

- Panda-Bild = **nur** Modul/Bereich.  
- Ampel = **nur** System-/Seitenstatus.  
- Ampel-Höhe ≤ ca. **20 %** der sichtbaren Panda-Höhe.  
- Keine kombinierten „Panda+Ampel“-Bitmaps.
