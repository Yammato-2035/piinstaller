# Developer Dashboard Tooling-Grenze (DE)

## Zweck

Das Developer Dashboard ist ein internes Entwicklungs-, Governance- und Evidence-Werkzeug. Es ist kein normales Setuphelfer-Produktfeature für Endnutzer.

## Verbindliche Regeln

1. Das Developer Dashboard ist **internes Tooling**.
2. Es ist **kein Bestandteil** der normalen Setuphelfer-Benutzeroberfläche.
3. Es darf nicht als Produktfeature beworben werden.
4. Es darf nicht in normale Nutzerflows wie Backup, Restore oder Rescue eingebunden werden.
5. Es stellt **keine freie Shell** bereit.
6. Es führt keine gefährlichen Aktionen direkt aus.
7. Es darf read-only Checks und sichere Tests nur allowlist-basiert starten.
8. Es darf Operator-Handoffs erzeugen, aber keine Operator-Aktionen ersetzen.
9. Jeder Command Run erzeugt Evidence.
10. Roadmap und Dashboard dürfen Status nur anhand von Evidence ändern.

## Explizite Verbote

- Keine freie Kommandoeingabe
- Keine Terminal-Eingabe-Emulation
- Kein `sudo` aus dem Dashboard-Runner
- Kein `apt install`/`upgrade`, kein `dd`, `mkfs`, `parted write`
- Keine Restore-/Backup-/USB-Write-Ausführung aus dem Developer Dashboard

## Cursor-Ausfuehrungsregel (verbindlich)

Cursor darf keine Background-Tasks, Auto-Efficiency-Ketten, Ingest-Jobs, Commit-/Push-Ketten oder spaetere Statusmeldungen ankuendigen oder starten.  
Jeder Lauf endet synchron mit vollstaendigem Schlussbericht.  
Wenn Operatorrechte noetig sind, wird nur ein Operator-Handoff erstellt, ohne Hintergrundausfuehrung.
