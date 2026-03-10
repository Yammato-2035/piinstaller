# Sudo-Komponenten – Nutzungsübersicht (Audit B-05/D-004)

Stand: Priorität-B-Fix

## Komponenten

| Komponente | Datei | Verwendung |
|------------|-------|------------|
| **SudoPasswordDialog** | `frontend/src/components/SudoPasswordDialog.tsx` | App-weit: ein Mal in `App.tsx`, z.B. für initiale Sudo-Passwort-Speicherung |
| **SudoPasswordModal** | `frontend/src/components/SudoPasswordModal.tsx` | Setup-Seiten: HomeAutomationSetup, ControlCenter, MonitoringDashboard, SettingsPage, NASSetup, BackupRestore, KinoStreaming, MusicBoxSetup, RaspberryPiConfig |

## Hauptpfad für Setup-Flows

- **SudoPasswordModal** ist der Hauptpfad für setup-spezifische Sudo-Abfragen (wird von vielen Setup-Seiten genutzt).
- **SudoPasswordDialog** dient der App-weiten Sudo-Passwortverwaltung.

## Spätere Vereinfachung

Bei künftiger Refaktor-Phase: Nutzungspfade prüfen und ggf. auf eine gemeinsame Komponente konsolidieren. Aktuell keine funktionale Änderung.
