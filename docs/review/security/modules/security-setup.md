# Security Review: SecuritySetup

## Kurzbeschreibung

Frontend-Seite SecuritySetup + Backend-Endpunkte für Sicherheits-Scan, Firewall (UFW) enable/install, Regeln add/delete, Konfiguration. Nutzer können Firewall aktivieren, Regeln hinzufügen/entfernen, Security-Status abfragen.

## Angriffsfläche

- API: POST /api/security/scan, /api/security/configure, /api/security/firewall/enable, install, rules, add, delete.
- Eingaben: Firewall-Regeln (Port, Richtung, Adresse), Konfigurationsoptionen.

## Schwachstellen

1. **Input Validation:** Firewall-Regeln (Port, IP/CIDR) müssen strikt validiert werden; ungültige oder bösartige Regeln könnten Dienstausfall oder Umgehung bewirken.
2. **Command Execution:** UFW-Befehle werden per run_command mit sudo ausgeführt; Befehle sollten aus Listen/Whitelist aufgebaut werden, keine ungeprüften Strings.
3. **Audit:** Keine explizite Audit-Log für Firewall-Änderungen (wer, wann, welche Regel).

## Empfohlene Maßnahmen

- Strikte Validierung: Port 1–65535, CIDR/IP-Format, erlaubte Aktionen (allow/deny, in/out).
- UFW-Befehle ausschließlich aus validierten Teilen bauen (Listen-Argumente).
- Optional: Audit-Einträge für Firewall-Änderungen (z. B. models/audit oder Log).

## Ampelstatus

**GELB.** Relevante Schwäche (Regel-Validierung, Audit); kein direkter Release-Blocker, da typischer Einsatz im vertrauenswürdigen LAN.

## Betroffene Dateien

- backend/app.py: /api/security/* (ca. 4259–5086+).
- frontend/src/pages/SecuritySetup.tsx.
