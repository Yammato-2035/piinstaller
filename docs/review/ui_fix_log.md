# UI Fix Log

## Priorität A

| ID | Datei/Bereich | Problem | Änderung | Test durchgeführt | Status |
|----|---------------|---------|----------|-------------------|--------|
| A1 | ControlCenter.tsx | Wifi Import fehlt | lucide-react Import ergänzt | WLAN-Sektion getestet | erledigt |
| A2 | ControlCenter.tsx | Performance ohne Hinweis für Einsteiger | Blurb „Nur für erfahrene Nutzer. Änderungen können Neustart erfordern.“ eingefügt | Build OK | erledigt |
| A3 | InstallationWizard.tsx | Fortschritts-/Statusanzeige | Bereits vorhanden: „Installation läuft“, Fortschrittsbalken, „X% abgeschlossen“ – keine Änderung | geprüft | erledigt |
| A4 | SettingsPage.tsx | „Initialisierung“ technischer Begriff | Bezeichnung zu „Ersteinrichtung“ geändert (Tab + Kartenüberschrift) | Build OK | erledigt |
| A5 | ControlCenter.tsx | Display: xrandr/DISPLAY/X-Session unklar | Intro „Bildschirm-Konfiguration (nur bei laufender Grafikumgebung)“; Fallback-Meldung nutzerfreundlich umformuliert | Build OK | erledigt |
| A6 | SudoPasswordModal.tsx, SudoPasswordDialog.tsx | Sudo-Dialog: unklarer Zweck | Subtitle „Wird für Installationen und Sicherheitseinstellungen benötigt.“ (Modal-Default + Dialog) | Build OK | erledigt |
| A7 | App.css, Dashboard.tsx, PeripheryScan.tsx | Statusfarben emerald vs green uneinheitlich | badge-success + Dashboard StatusItem + PeripheryScan OK-Anzeigen auf emerald-* umgestellt (graphics_system #10b981) | Build OK | erledigt |
| A8 | SettingsPage.tsx | Überfüllter Screen, Begriff „Initialisierung“ | Mit A4 abgedeckt (Ersteinrichtung); Tab-Struktur geprüft – keine strukturierende Änderung (Regel: kein UI-Redesign) | geprüft | erledigt |
