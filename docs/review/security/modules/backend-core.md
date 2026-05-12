# Security Review: Backend Core / API

## Kurzbeschreibung

Monolithisches FastAPI-Backend (app.py) mit allen API-Routen, run_command-Wrapper für Systembefehle, Sudo-Store-Integration, CORS, TrustedHost, Security-Header. Zusätzlich api/routes (pairing, sessions, devices, modules, actions, ws) für Remote-Funktionen.

## Angriffsfläche

- Alle HTTP-Endpunkte (GET/POST/PUT/DELETE); WebSocket für Remote.
- Request-Bodies (JSON): Passwörter, Usernames, Pfade, URLs, Firewall-Regeln, Konfigurationen.
- Query-Parameter und Headers (Host, Origin).
- subprocess/run_command mit Nutzerdaten oder festen Befehlen; teilweise shell=True (dokumentiert).

## Schwachstellen

1. **Command Execution:** run_command(cmd, ...) – cmd teils aus Listen (sicher), teils aus String-Konkatenation; vereinzelt noch shell-ähnliche Aufrufe (z. B. wlr-randr, ss -tuln). Bereits gehäuft auf Listen umgestellt (hostname, Temperatur, curl).
2. **Input Validation:** Unterschiedlich je Endpoint; Pfad-Parameter (Backup, NAS, Logs) können Path-Traversal-Risiko haben, wenn nicht strikt validiert.
3. **Rechte:** Keine RBAC; wer die API erreicht (localhost/LAN), kann alle Endpunkte nutzen. Sudo nur mit gespeichertem Passwort oder manueller Ausführung.
4. **Fehlerbehandlung:** Teilweise Exception-Messages an Client (Risiko Information Disclosure).
5. **Logging:** Sensible Daten (Passwörter) nicht loggen; andere Request-Daten teils in Logs.

## Empfohlene Maßnahmen

- Alle verbleibenden shell-Art-Aufrufe auf Listen umstellen oder mit shlex.quote absichern; keine Nutzerdaten in Befehlsstrings.
- Strikte Pfad-Validierung (Whitelist, realpath, kein Verlassen von erlaubten Bäumen) für alle Endpunkte mit Pfad-Parametern.
- Host-Validierung (TrustedHost) beibehalten; CORS restriktiv halten.
- Keine Passwörter oder Tokens in Logs; Redaction prüfen (debug/redaction.py).

## Ampelstatus

**GELB.** Keine kritische, direkt ausnutzbare RCE ohne Voraussetzungen; Abhängigkeit von Netzwerkzugang und ggf. Sudo-Passwort. Härtung (shell, Pfade) reduziert Risiko weiter.

## Betroffene Dateien / Code-Stellen

- backend/app.py: run_command (ca. Zeile 2251), alle @app.*-Routen; subprocess.Popen/Run; TrustedHostMiddleware; CORS.
- backend/core/sudo_store.py: Speicherung/Abruf Sudo-Passwort.
- backend/core/auth.py, api/routes/*: Remote-Auth, Pairing.
