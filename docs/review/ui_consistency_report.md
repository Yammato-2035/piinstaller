# UI Consistency Report

_Automatische UI-Konsistenzprüfung – Analyse ohne Code-Änderungen_

---

## Zusammenfassung

| Kategorie | Anzahl Inkonsistenzen |
|-----------|----------------------|
| Icons | 18 |
| Farben | 12 |
| Buttons | 15 |
| Layout | 8 |
| Navigation | 5 |
| Begriffe | 9 |
| **Gesamt** | **67** |

---

## Icons

### UI-CHECK: inkonsistenter Iconstil

**Gemischte Icon-Quellen:** Die Anwendung nutzt zwei Icon-Systeme parallel:
- **AppIcon** (Custom SVG aus `assets/icons/`) – einheitlicher Stil gemäß graphics_system.md
- **Lucide React** – externes Icon-Set mit eigenem Stil

| Datei | Verwendung | Problem |
|-------|------------|---------|
| ControlCenter.tsx | Wifi-Section nutzt AppIcon (device_wifi), Scan-Button nutzt Lucide `<Wifi />` | **Kritisch:** Wifi ist nicht importiert – Referenz führt zu Laufzeitfehler |
| PeripheryScan.tsx | AppIcon für Titel + Prozess; Lucide (Cpu, Keyboard, Mouse, Camera, Headphones, Scan, etc.) für Kategorien | Zwei Stile auf einer Seite |
| BackupRestore.tsx | AppIcon nur für USB-Überschrift; Lucide (Cloud, Database, HardDrive, Lock, etc.) für alle weiteren Icons | Inkonsistent |
| Dashboard.tsx | AppIcon + Lucide (Cpu, HardDrive, Zap, Thermometer, Wind, Monitor, Package) gemischt | Unterschiedliche Linienstärken und Formen |
| MonitoringDashboard.tsx | Nur Lucide (CheckCircle, AlertCircle) – kein AppIcon für Status | Status-Icons nicht aus definiertem System |
| MailServerSetup.tsx | Nur Lucide (CheckCircle, AlertCircle) | Status-Icons nicht aus AppIcon |
| UserManagement.tsx | Nur Lucide | Keine AppIcon-Integration |
| SudoPasswordDialog.tsx | Nur Lucide (AlertCircle) | Fehler-/Warn-Icons nicht aus AppIcon |
| SettingsPage.tsx | AppIcon + Lucide (CheckCircle, RefreshCw) gemischt | Inkonsistent |

### UI-CHECK: inkonsistente Icongröße

| Kontext | Soll (gem. icon_usage.md) | Ist | Datei |
|---------|---------------------------|-----|-------|
| Navigation (Sidebar) | 24px | 24px ✓ / 18px (Lucide fallback) | Sidebar.tsx |
| Status | 16px oder 24px | 18px, 20px, 14px, 12px | Diverse |
| Diagnose (Logs-Tab) | – | 18px | SettingsPage.tsx |
| Prozess „Assimilation starten“ | 24px (Prozess) | 24px ✓ | PeripheryScan.tsx |
| Prozessschritte Assistent | 48px | 48px ✓ | InstallationWizard.tsx |
| Lucide-Icons | – | 12, 14, 16, 18, 20, 22, 24, 36, 48 | Diverse – keine einheitliche Größenstufe |
| Clock (BackupRestore) | – | 48px | BackupRestore.tsx |
| Mail (MailServerSetup) | – | 48px | MailServerSetup.tsx |
| Search (HomeAutomationSetup) | – | 36px | HomeAutomationSetup.tsx – abweichend |
| SudoPasswordModal Lock | – | 22px | SudoPasswordModal.tsx – ungerade Größe |

---

## Farben

### UI-CHECK: inkonsistente Statusfarbe

| Regel | Hex | Verwendung |
|-------|-----|------------|
| OK | #10b981 | Grün |
| Warnung | #f59e0b | Gelb |
| Fehler | #ef4444 | Rot |
| Info | #3b82f6 | Blau |
| Deaktiviert | #64748b | Grau |

**Inkonsistenzen:**

| Datei | Problem |
|-------|---------|
| PeripheryScan.tsx | `emerald-*` statt `green-*` für OK/Success (emerald-600, emerald-500, emerald-400, emerald-900) – Abweichung von Grün-Palette |
| PeripheryScan.tsx | `amber-*`, `purple-*` für Kategorien (Keyboard amber, Mouse purple, Cpu sky) – semantische Farben für Nicht-Status |
| BackupRestore.tsx | `green-600`, `green-700` für Erfolg – korrekt, aber `emerald` in anderen Bereichen |
| Dashboard.tsx | `emerald-*` für Status-Badges (z. B. „Alles OK“) – sollte einheitlich `green-*` oder emerald durchgängig sein |
| Badge (App.css) | `badge-success` = green-900/green-200; `badge-warning` = yellow-900/yellow-200; `badge-info` = blue-900 – Tailwind nutzt teils „amber“ für Warnung |
| RaspberryPiConfig.tsx | `orange-600` für Neustart-Button – außerhalb der definierten Statuspalette |
| ControlCenter.tsx (WLAN-Scan) | `purple-600` statt sky für primäre Aktion – inkonsistent |
| BackupRestore.tsx | `purple-*` für Cloud-Badge, `sky-*` für lokale Backups – verschiedene Kontexte |

### UI-CHECK: Primärfarbe uneinheitlich

- Primärfarbe lt. graphics_system: Sky #0284c7
- Verwendung: sky-400, sky-500, sky-600, sky-300 – unterschiedliche Helligkeitsstufen ohne klare Regel
- PeripheryScan: emerald als Akzentfarbe statt sky

---

## Buttons

### UI-CHECK: inkonsistenter Buttonstil

| Problem | Beispiele |
|---------|-----------|
| Verschiedene Padding-Varianten | `px-3 py-2`, `px-4 py-2`, `px-4 py-3`, `px-6 py-3` |
| Unterschiedliche Hover-Farben | `hover:bg-sky-500` vs `hover:bg-sky-700` (btn-primary) |
| Inkonsistente Primär-Buttons | `bg-sky-600` vs `bg-emerald-600` (PeripheryScan) vs `bg-purple-600` (WLAN-Scan) |
| Sekundär-Buttons | `bg-slate-700` vs `bg-slate-700/50` vs `bg-slate-700/60` |
| Danger-Buttons | `bg-red-600` vs `bg-red-600/25` mit border |
| Fehlende Nutzung von .btn-primary | Viele Buttons nutzen Inline-Styles statt App.css-Klassen |
| Schriftgrößen | `text-sm`, `font-medium`, `font-semibold` uneinheitlich |

**Konkrete Abweichungen:**

| Datei | Button | Abweichung |
|-------|--------|------------|
| PeripheryScan.tsx | „Assimilation starten“ | `bg-emerald-600` statt sky – einziger grüner Primär-Button |
| ControlCenter.tsx | „Netzwerke scannen“ | `bg-purple-600` |
| RaspberryPiConfig.tsx | Neustart | `bg-orange-600` |
| BackupRestore.tsx | Abbruch | `bg-red-600/25 border` – abweichender Danger-Stil |

---

## Layout

### UI-CHECK: inkonsistente Layoutabstände

| Problem | Beispiele |
|---------|-----------|
| Padding-Kombinationen | `p-4`, `p-6`, `p-3`, `px-4 py-2` – viele Varianten |
| Gaps | `gap-2`, `gap-3`, `gap-4`, `gap-6` – keine festen Stufen |
| Margins | `mb-2`, `mb-4`, `mb-6`, `mt-2`, `mt-3`, `mt-4` |
| Card-Padding | `.card` hat `padding: 1.5rem`; manche Cards nutzen zusätzlich `p-4`, `p-6` |
| Tab-Abstände | SettingsPage Tabs: `px-4 py-2` vs Sub-Tabs `px-3 py-1.5` |

### UI-CHECK: unterschiedliche Rundungen

- `rounded-lg`, `rounded-xl`, `rounded-2xl`, `rounded-md`, `rounded-full` – keine einheitliche Stufung

---

## Navigation

### UI-CHECK: Navigationsstruktur inkonsistent

| Problem | Details |
|---------|---------|
| Doppelte Semantik | „Monitoring“ und „Peripherie-Scan“ nutzen beide `icon_diagnose` – gleiches Icon für unterschiedliche Bereiche |
| Modus-abhängige Sichtbarkeit | Grundlagen/Erweitert/Diagnose blenden Menüpunkte ein/aus – Nutzer können sich „verirren“, wenn Modus wechselt |
| Benennung | „Assistent“ vs „Installationsassistent“ (Seitentitel) – unterschiedliche Bezeichnungen |
| „Raspberry Pi Config“ vs „Raspberry Pi Konfiguration“ | Sidebar: „Raspberry Pi Config“, Seiten-Header: „Raspberry Pi Konfiguration“ |

---

## Begriffe

### UI-CHECK: inkonsistente Begriffsnutzung

| Begriffskonflikt | Fundstellen | Empfehlung |
|------------------|-------------|------------|
| Speichern / Übernehmen / Anwenden | ControlCenter: „Übernehmen“ (Display), „Speichern“ (Tastatur); SecuritySetup: „Anwenden“; NASSetup: „Konfiguration anwenden“; SettingsPage: „Speichern“ | Laut ux_guidelines: Speichern (persist), Übernehmen (sofort), Anwenden (Konfig) – Nutzer unterscheiden evtl. nicht |
| Konfigurieren / Konfiguration anwenden | NASSetup: „Konfiguration anwenden“; WebServerSetup: „Konfiguration anwenden“; DevelopmentEnv: „Konfigurieren“ | Einheitlich „Konfiguration anwenden“ oder „Einstellungen übernehmen“ |
| Module / Komponenten / Dienste | Dashboard: „Module Übersicht“; MonitoringDashboard: „Komponenten“; UserManagement: „Systembenutzer / Dienste“; PeripheryScan: „Komponenten“ | Klarheit: Module = installierbare Einheiten, Komponenten = Hardware/Software-Teile, Dienste = Hintergrundprozesse |
| Backend / Server | Vereinzelt noch „Backend“ in Toasts/Fehlermeldungen | Durchgängig „Server“ |

---

## Priorisierte Liste

### Priorität A – kritisch

1. **ControlCenter.tsx:** `Wifi` wird verwendet, ist aber nicht aus lucide-react importiert → Laufzeitfehler beim Öffnen der WLAN-Sektion
2. **Icon-Mix:** Zwei Icon-Systeme (AppIcon + Lucide) auf denselben Screens – visuell uneinheitlich
3. **Statusfarben:** emerald vs green – uneinheitliche „OK“-Farbe

### Priorität B – mittel

4. PeripheryScan: emerald statt sky als Primärfarbe
5. ControlCenter: purple für WLAN-Scan-Button
6. RaspberryPiConfig: orange für Neustart
7. Button-Padding uneinheitlich (px-3/py-2 vs px-4/py-3)
8. Speichern/Übernehmen/Anwenden – Begriffsinkonsistenz
9. Lucide-Icons in Statuskontexten (CheckCircle, AlertCircle) statt AppIcon status_*

### Priorität C – kosmetisch

10. Icongrößen 14, 18, 22 statt Standardstufen (16, 24, 32, 48)
11. „Raspberry Pi Config“ vs „Raspberry Pi Konfiguration“
12. Abweichende Rundungen (rounded-md vs rounded-lg)
13. gap-Varianten ohne einheitliche Skala

---

## Wichtigste UI-Probleme (Top 20)

1. **ControlCenter: fehlender Wifi-Import** – Laufzeitfehler
2. Gemischte Icon-Systeme (AppIcon + Lucide) auf vielen Seiten
3. emerald vs green für OK/Erfolg – inkonsistente Statusfarbe
4. PeripheryScan nutzt emerald als Akzent statt sky
5. WLAN-Scan-Button purple statt sky
6. Neustart-Button orange – außerhalb Farbpalette
7. Speichern/Übernehmen/Anwenden – drei Begriffe für ähnliche Aktionen
8. btn-primary/btn-secondary werden nicht durchgängig genutzt
9. Lucide-Status-Icons (CheckCircle, AlertCircle) statt AppIcon
10. Icongrößen 12, 14, 18, 22, 36 – nicht in Standardstufen
11. „Raspberry Pi Config“ vs „Raspberry Pi Konfiguration“
12. Monitoring + Peripherie-Scan: gleiches Icon (diagnose)
13. Verschiedene Button-Paddings ohne System
14. purple/amber für Kategorien in PeripheryScan – semantisch unklar
15. Cloud-Badge purple vs Sky für lokale Backups
16. Unterschiedliche Danger-Button-Varianten
17. Gap/Padding ohne einheitliche Skala
18. „Backend“ vs „Server“ in Meldungen
19. Module/Komponenten/Dienste – Begriffsvermischung
20. SudoPasswordModal: Lock 22px – ungerade Größe

---

## Anhang: Analysebasis

- **Quellen:** frontend/src (TSX, CSS)
- **Referenz:** docs/design/graphics_system.md, docs/design/icon_usage.md
- **Zeitpunkt:** Analyse ohne Code-Änderungen
- **Methodik:** Grep/Suche nach Icons, Farben, Buttons, Begriffen, Abständen
