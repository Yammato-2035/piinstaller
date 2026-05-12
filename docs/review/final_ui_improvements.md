# Priorisierte Nachbesserung

_Phase 10 – Konsolidierte Verbesserungsliste aus UX-Lint, UI-Konsistenz und visueller UX_

---

## Reihenfolge der Umsetzung

**Strikte Reihenfolge:** Priorität A → B → C

---

## Priorität A – kritisch

### A1. ControlCenter: fehlender Wifi-Import (Laufzeitfehler)
- **Ort:** `frontend/src/pages/ControlCenter.tsx`
- **Problem:** `<Wifi size={16} />` wird verwendet, `Wifi` ist nicht aus `lucide-react` importiert
- **Maßnahme:** `import { ..., Wifi } from "lucide-react";` ergänzen
- **Quelle:** ui_consistency_report

### A2. Control Center Performance: Hilfetext
- **Ort:** `ControlCenter.tsx` – Performance-Bereich (Governor, Overclocking, Swap)
- **Problem:** Kein Hinweis für Einsteiger – hohes Fehlbedienungsrisiko
- **Maßnahme:** Blurb einfügen: „Nur für erfahrene Nutzer. Änderungen können Neustart erfordern.“
- **Quelle:** ux_lint_report

### A3. InstallationWizard: Fortschritts-/Statusanzeige
- **Ort:** `InstallationWizard.tsx`
- **Problem:** Kein klarer Fortschrittsbalken / Ladeindikator während Installation
- **Maßnahme:** „Installation läuft…“ + Fortschrittsbalken oder Ladeindikator sicherstellen
- **Quelle:** ux_lint_report

### A4. SettingsPage „Initialisierung“
- **Ort:** `SettingsPage.tsx`
- **Problem:** Technischer Begriff für Ersteinrichtung
- **Maßnahme:** Bezeichnung zu „Ersteinrichtung“ oder „Systemstatus“ ändern
- **Quelle:** ux_lint_report

### A5. Control Center Display: xrandr-Erklärung
- **Ort:** `ControlCenter.tsx` – Display-Bereich
- **Problem:** „xrandr“, „DISPLAY“, „X-Session“ ohne Erklärung – Anfänger verstehen nicht
- **Maßnahme:** Kurze Erklärung: „Bildschirm-Konfiguration (nur bei laufender Grafikumgebung)“
- **Quelle:** ux_lint_report

### A6. Sudo-Dialog: optionaler Hinweis
- **Ort:** Sudo-Passwort-Dialog
- **Problem:** Einsteiger verstehen evtl. nicht, wofür Administrator-Rechte
- **Maßnahme:** Optionaler Hinweis: „Wird für Installationen und Sicherheitseinstellungen benötigt.“
- **Quelle:** ux_lint_report

### A7. Statusfarben: emerald vs green
- **Ort:** PeripheryScan, Dashboard, Badge
- **Problem:** Uneinheitliche „OK“-Farbe (emerald vs green)
- **Maßnahme:** Einheitlich `green-*` oder durchgängig `emerald-*` – graphics_system.md folgen
- **Quelle:** ui_consistency_report

### A8. SettingsPage: überfüllter Screen
- **Ort:** SettingsPage – Init, Netzwerk, Basic, Screenshots
- **Problem:** Begriff „Initialisierung“ überfordert + viele Tabs
- **Maßnahme:** Wie A4 – Begriff vereinfachen; Tab-Struktur prüfen
- **Quelle:** ux_lint_report

---

## Priorität B – sinnvoll

### B1. „Backend“ durch „Server“ ersetzen (Restbestände)
- **Ort:** Toasts, Fehlermeldungen
- **Maßnahme:** Durchgängig „Server“ statt „Backend“
- **Quelle:** ux_lint_report, ui_consistency_report

### B2. SecuritySetup: Button „Anwenden“
- **Ort:** `SecuritySetup.tsx` ~358
- **Maßnahme:** „Sicherheitseinstellungen übernehmen“ statt „✓ Anwenden“
- **Quelle:** ux_lint_report

### B3. DsiRadioSettings: Fehlermeldung
- **Ort:** `DsiRadioSettings.tsx`
- **Maßnahme:** „Einstellungen konnten nicht gespeichert werden. Bitte Verbindung prüfen.“
- **Quelle:** ux_lint_report

### B4. BackupRestore: Timeout-Meldung
- **Ort:** `BackupRestore.tsx`
- **Maßnahme:** „Die Aktion hat zu lange gedauert. Server prüfen oder ‚Ohne Prüfung speichern‘ probieren.“
- **Quelle:** ux_lint_report

### B5. PeripheryScan: Console-Fehlermeldung
- **Ort:** `PeripheryScan.tsx`
- **Maßnahme:** „Der Server ist nicht erreichbar. Bitte starten Sie ihn (./start-backend.sh).“
- **Quelle:** ux_lint_report

### B6. RunningBackupModal: Abbruch-Feedback
- **Ort:** `RunningBackupModal` (BackupRestore)
- **Maßnahme:** Klare Meldung „Backup wird abgebrochen…“ beim Abbruch
- **Quelle:** ux_lint_report, visual_ux_improvements

### B7. Clone-Bereich: Fortschritts-/Statuszeile
- **Ort:** BackupRestore – Klonen
- **Maßnahme:** Statuszeile „Klon läuft… X%“ während laufendem Klon
- **Quelle:** visual_ux_improvements

### B8. PeripheryScan: emerald statt sky als Primärfarbe
- **Ort:** „Assimilation starten“ Button
- **Maßnahme:** `bg-sky-600` statt `bg-emerald-600` (graphics_system)
- **Quelle:** ui_consistency_report

### B9. ControlCenter: WLAN-Scan-Button purple
- **Ort:** ControlCenter – WLAN
- **Maßnahme:** `bg-sky-600` statt `bg-purple-600`
- **Quelle:** ui_consistency_report

### B10. RaspberryPiConfig: Neustart-Button orange
- **Ort:** `RaspberryPiConfig.tsx`
- **Maßnahme:** `bg-amber-600` (Warnung) oder sky – außerhalb Palette prüfen
- **Quelle:** ui_consistency_report

### B11. Settings „Zurücksetzen“
- **Ort:** SettingsPage – API-URL
- **Maßnahme:** „Auf Standard zurücksetzen“
- **Quelle:** ux_lint_report

### B12. BackupRestore confirmText
- **Ort:** BackupRestore ~542
- **Maßnahme:** „USB vorbereiten“ oder „Formatierung starten“ statt „Weiter“
- **Quelle:** ux_lint_report

### B13. Icon-Mix: AppIcon vs Lucide
- **Ort:** Dashboard, PeripheryScan, BackupRestore, ControlCenter, etc.
- **Maßnahme:** Schrittweise AppIcon für Status (status_ok, status_warning) nutzen statt Lucide CheckCircle/AlertCircle
- **Quelle:** ui_consistency_report

### B14. Speichern/Übernehmen/Anwenden
- **Ort:** ControlCenter, SecuritySetup, NASSetup
- **Maßnahme:** Dokumentierte Regel (Speichern=persist, Übernehmen=sofort, Anwenden=Konfig) – optional Tooltips
- **Quelle:** ui_consistency_report

---

## Priorität C – kosmetisch

### C1. „Weiter“ in Dialogen
- **Ort:** InstallationWizard, BackupRestore (wo Kontext unklar)
- **Maßnahme:** Spezifischer: z. B. „Formatierung starten“
- **Quelle:** ux_lint_report

### C2. „Config“ vs „Konfiguration“
- **Ort:** RaspberryPiConfig, Settings
- **Maßnahme:** Einheitlich „Konfiguration“ in Beschriftungen
- **Quelle:** ux_lint_report

### C3. ModulePage: konkretere Fehlermeldung
- **Ort:** ModulePage (Remote)
- **Maßnahme:** Ursache aus Backend anzeigen
- **Quelle:** ux_lint_report

### C4. Icongrößen 14, 18, 22
- **Ort:** Diverse
- **Maßnahme:** Auf Standardstufen 16, 24, 32, 48 angleichen
- **Quelle:** ui_consistency_report

### C5. „Raspberry Pi Config“ vs „Raspberry Pi Konfiguration“
- **Ort:** Sidebar vs Seiten-Header
- **Maßnahme:** Einheitliche Bezeichnung
- **Quelle:** ui_consistency_report

### C6. BackupRestore: Einleitungstext pro Tab
- **Ort:** BackupRestore
- **Maßnahme:** Kurzer Einleitungstext pro Tab (z. B. „Hier erstellen Sie Backups…“)
- **Quelle:** visual_ux_improvements

### C7. Modus-Tab „Erweitert“: Tooltip
- **Ort:** Sidebar – Erweitert
- **Maßnahme:** „Technische Einstellungen für erfahrene Nutzer“
- **Quelle:** visual_ux_improvements

### C8. Button-Padding / Rundungen / Gaps
- **Ort:** Diverse
- **Maßnahme:** Einheitliche Stufung (px-4 py-2, gap-4, rounded-lg) wo möglich
- **Quelle:** ui_consistency_report

### C9. HelpTooltip-Abdeckung
- **Ort:** RaspberryPiConfig Overclocking, BackupRestore Verschlüsselung, etc.
- **Maßnahme:** HelpTooltip für technische Optionen ergänzen
- **Quelle:** ux_lint_report

### C10. ControlCenter / RaspberryPiConfig: Kategorien-Gruppierung
- **Ort:** ControlCenter, RaspberryPiConfig
- **Maßnahme:** Optionale Gruppierung der Bereiche
- **Quelle:** visual_ux_improvements, ux_lint_report

---

## Umsetzungsempfehlung

| Phase | Priorität | Geschätzte Aufwände |
|-------|-----------|----------------------|
| Sofort | A1 | 1 Zeile Code (Wifi-Import) |
| Kurz | A2–A8 | Je 5–20 Min |
| Mittel | B1–B14 | Je 10–30 Min |
| Lang | C1–C10 | Je 5–15 Min (optional) |

**Hinweis:** A1 ist ein Bugfix und sollte vor allen anderen umgesetzt werden.
