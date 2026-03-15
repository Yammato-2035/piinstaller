# Security Review: SudoPasswordDialog / Sudo Store

## Kurzbeschreibung

Frontend-Dialog für Sudo-Passwort; Backend speichert verschlüsselt (Fernet), TTL, Rate-Limit auf POST.

## Angriffsfläche

Eingaben: Passwort (POST /api/users/sudo-password). Nie im Klartext loggen.

## Schwachstellen

Bereits abgesichert: Verschlüsselung, TTL, Rate-Limit. Key-Datei nur User-lesbar.

## Ampelstatus

**GRÜN.** Betroffene Dateien: backend/core/sudo_store.py, app.py /api/users/sudo-password, frontend SudoPasswordDialog.
