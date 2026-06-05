# KB — Windows Explorer / Shell Failures (Inspect-only)

## Typische Indikatoren (read-only)

| Symptom | Diagnosecode |
|---------|----------------|
| `explorer.exe` fehlt | `WIN-EXPLORER-001` |
| `explorer.exe` nicht lesbar | `WIN-EXPLORER-002` |
| Winlogon `Shell` verdächtig | `WIN-SHELL-001` |
| `Userinit` verdächtig | `WIN-SHELL-002` |

## Vorschläge (keine Ausführung)

- Daten zuerst sichern (Dry-Run-Manifest)
- WinRE starten (Operator)
- Offline-SFC/DISM nur als **Vorschlag** mit Build-/Quellen-Hinweis
- Kein automatisches Registry-Patching aus Rescue

Evidence: `windows_inspect_diagnostic_codes.json`
