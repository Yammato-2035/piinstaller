# Security Review: BackupRestore

## Kurzbeschreibung

Backup und Wiederherstellung: Jobs, Einstellungen, Cloud-Ziele, USB-Mount, Clone, Zielprüfung. Backend führt rsync, tar, mount, Cloud-API-Calls aus; nutzt Pfade und optional Credentials.

## Angriffsfläche

- API: Backup-Jobs, settings, schedule/run-now, cloud (test, list, delete, verify), targets, target-check, clone, usb (mount, prepare).
- Eingaben: Pfade (lokal/remote), Cloud-Credentials (URL, Token/Passwort), Dateinamen.

## Schwachstellen

1. **Path Traversal:** Alle Pfad-Eingaben müssen validiert werden (realpath, Unterpfad von erlaubten Basen); keine relativen Pfade wie "../../etc/passwd".
2. **Credentials in Logs:** Cloud-Tokens/Passwörter dürfen nicht in Logs oder Fehlerantworten erscheinen.
3. **Netzwerk:** Cloud-Endpunkte (z. B. Nextcloud) – URL-Validierung, nur HTTPS wo möglich.
4. **USB/Mount:** mount-Befehle nur mit validierten Geräten/Pfaden; keine Nutzer-Pfade in mount-Point ohne Prüfung.

## Empfohlene Maßnahmen

- Strikte Pfad-Normalisierung und Whitelist (z. B. nur unter /home, /media, konfigurierte Backup-Basis).
- Redaction für alle Credential-Felder in Logs und in API-Responses (z. B. nur "gesetzt" vs. Wert).
- URL-Validierung: Schema https, erlaubte Hosts oder Platzhalter.

## Ampelstatus

**GELB.** Relevante Schwächen (Pfade, Credentials); kein ROT, wenn keine direkte Path-Traversal-Lücke nachgewiesen.

## Betroffene Dateien

- backend/app.py: /api/backup/* (viele Routen).
- backend/modules/backup.py falls verwendet.
- frontend/src/pages/BackupRestore.tsx.
