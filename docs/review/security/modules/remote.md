# Security Review: RemoteView / Remote-Funktionen

## Kurzbeschreibung

Linux Companion: Pairing, Sessions, Geräte, Module, Aktionen, WebSocket. API unter api/routes (pairing, sessions, devices, modules, actions, ws). Ermöglicht Remote-Steuerung nach Pairing und Berechtigungen.

## Angriffsfläche

- Pairing (QR, Tokens), Session-Verwaltung, Aufruf von Aktionen auf dem Pi von außen.
- WebSocket: Echtzeit-Kommunikation; mögliche Payload-Injection wenn Aktionen nicht validiert werden.

## Schwachstellen

1. **Autorisierung:** Jede Aktion muss gegen Berechtigungen (core/permissions) geprüft werden; keine Umgehung für privilegierte Aktionen.
2. **Token:** Pairing-Token und Session-Tokens sicher speichern; Rotation/Ablauf.
3. **Input:** Aktionen mit Parametern (z. B. Modul, Befehl) müssen strikt validiert werden (Whitelist Modul/Aktion).
4. **Audit:** Wichtig für Remote: Wer hat welche Aktion von welchem Gerät ausgelöst.

## Empfohlene Maßnahmen

- Strikte Permission-Checks vor Ausführung jeder Remote-Aktion.
- Keine Rohbefehle von Remote ausführbar; nur definierte Module/Aktionen.
- Token-Rotation und Ablauf; Audit-Log für Remote-Aktionen.

## Ampelstatus

**GELB.** Relevante Schwächen (Validierung Aktionen, Audit); kein ROT wenn Permissions-Modell konsequent umgesetzt.

## Betroffene Dateien

- backend/api/routes/pairing.py, sessions.py, devices.py, modules.py, actions.py, ws.py.
- backend/core/auth.py, permissions.py.
- frontend/src/features/remote/*.
