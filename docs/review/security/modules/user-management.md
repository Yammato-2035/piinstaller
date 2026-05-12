# Security Review: UserManagement

## Kurzbeschreibung

Benutzerverwaltung: Anzeige, Anlegen, Löschen von Systembenutzern; Sudo-Passwort speichern (verschlüsselt). Endpunkte: /api/users, /api/users/create, /api/users/{username} (DELETE), /api/users/sudo-password (check, store).

## Angriffsfläche

- API: GET/POST/DELETE mit Username, Passwort (sudo und User-Passwort).
- Eingaben: Username (Zeichen, Länge), Passwörter (Klartext beim Speichern, dann verschlüsselt).

## Schwachstellen

1. **Username-Validierung:** Username muss sicher für useradd/userdel sein (alphanumerisch, keine Shell-Metazeichen); Länge und Zeichensatz prüfen.
2. **Passwortstärke:** Keine erzwungene Komplexität für neue Benutzer; schwache Passwörter möglich.
3. **Rate-Limit:** Sudo-Password-Endpoint hat Rate-Limit; Create/Delete ggf. ebenfalls begrenzen gegen Brute-Force/DoS.
4. **Information Disclosure:** Fehlermeldungen bei useradd/userdel nicht zu detailliert (z. B. "user exists" vs. generisch).

## Empfohlene Maßnahmen

- Username: Whitelist (z. B. [a-zA-Z0-9_-], max Länge), keine Pfad-/Befehlsteile.
- Optional: Passwortstärke-Check vor Erstellung; Hinweis im UI.
- Rate-Limit für create/delete beibehalten oder ergänzen.
- Generische Fehlermeldungen nach außen.

## Ampelstatus

**GELB.** Relevante Schwächen (Validierung, Passwortstärke); Sudo-Store selbst gut abgesichert (verschlüsselt, TTL).

## Betroffene Dateien

- backend/app.py: /api/users/*, run_command(useradd, userdel, chpasswd).
- backend/core/sudo_store.py.
- frontend/src/pages/UserManagement.tsx, SudoPasswordDialog.
