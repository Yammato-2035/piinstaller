# Security Review: InstallationWizard

## Kurzbeschreibung

Setup-Assistent (wizard): Mehrstufige Installation über /api/install/start und /api/install/progress. Führt umfangreiche Systemänderungen (Pakete, Dienste, Konfiguration) per run_command aus.

## Angriffsfläche

- API: POST /api/install/start (Payload mit Auswahl/Optionen), GET /api/install/progress.
- Eingaben: Ausgewählte Komponenten, Optionen; Backend baut daraus Befehle.

## Schwachstellen

1. **Command Injection:** Alle Nutzer-Eingaben, die in Befehle einfließen, müssen validiert/gequotet werden; keine freie String-Konkatenation in shell-Befehlen.
2. **Umfang:** Viele Schritte mit sudo; Fehler in einem Schritt können System instabil lassen.
3. **Idempotenz:** Unklar ob Wiederholung bei Abbruch sicher ist.

## Empfohlene Maßnahmen

- Nur whitelistete Optionen/IDs in Befehle übernehmen; Listen-Argumente für subprocess.
- Klare Dokumentation der Install-Schritte und Fehlerbehandlung.

## Ampelstatus

**GELB.** Abhängig von Implementierung (Validierung der Start-Payload). Kein ROT wenn keine Nutzer-Strings in Befehle.

## Betroffene Dateien

- backend/app.py: /api/install/start, /api/install/progress (ca. 6636+).
- frontend/src/pages/InstallationWizard.tsx.
