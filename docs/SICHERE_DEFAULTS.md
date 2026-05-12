# Sichere Defaults (Milestone 3 – Transformationsplan)

Dieses Dokument beschreibt die **sicheren Standardeinstellungen** des PI-Installers und wie sie umgesetzt werden.

## Ziele

- **Firewall:** Standardmäßig alle Ports geschlossen außer 80 (HTTP), 443 (HTTPS) und ggf. 22 (SSH) nur wenn gewünscht.
- **SSH:** Empfehlung: Zugang nur mit Key, nicht mit Passwort (Option in Sicherheit).
- **Automatische Updates:** Standardmäßig EIN (tägliche Sicherheitsupdates).
- **Apps:** Jede App idealerweise mit eigenem Linux-User (bei Docker-Apps: Container-Isolation).
- **Daily Security Scan:** Einfache Reports (z. B. über Sicherheits-Seite oder Einstellungen).

## Umsetzung im PI-Installer

### Firewall (UFW)

- Unter **Sicherheit** kann UFW aktiviert und konfiguriert werden.
- **Empfohlene Defaults nach Erstinstallation:**  
  `ufw default deny incoming`  
  `ufw allow 80/tcp`  
  `ufw allow 443/tcp`  
  `ufw allow 22/tcp` nur wenn SSH von außen gewünscht.
- PI-Installer-Frontend (z. B. Port 3001) und Backend (8000) sollten nur im LAN oder über Reverse-Proxy (80/443) erreichbar sein.

### SSH-Härtung

- Unter **Sicherheit** → SSH: Option „Passwort-Login deaktivieren“ (nur Key-Login) empfohlen.
- Dokumentation: Siehe **INSTALL.md** und Sicherheits-Seite in der App.

### Automatische Updates

- Unter **Sicherheit** kann „Automatische Sicherheitsupdates“ aktiviert werden (unattended-upgrades).
- Default in der Konfiguration: aktivieren, damit Einsteiger geschützt sind.

### Daily Security Scan

- Einfacher Scan: z. B. `apt list --upgradable`, offene Ports, UFW-Status.
- Kann als Cron-Job oder über die Sicherheits-Seite („Scan ausführen“) angeboten werden.
- Reports: Anzeige in der App unter Sicherheit oder Einstellungen.

### App-Isolation (Docker)

- Bei Docker-basierter App-Installation (Phase 2.2) läuft jede App in einem eigenen Container.
- Kein gemeinsamer System-User nötig; Volumes für persistente Daten unter `/data/<appname>/`.

## Checkliste für Admins

- [ ] Firewall (UFW) aktiviert, nur 80/443 (und ggf. 22) offen
- [ ] SSH nur mit Key (Passwort-Login deaktiviert)
- [ ] Automatische Updates aktiviert
- [ ] Standard-Passwort des Pi-Benutzers geändert
- [ ] PI-Installer nur im LAN oder hinter Reverse-Proxy (HTTPS) erreichbar

## Siehe auch

- **Sicherheit** (in der App)
- **INSTALL.md** – Sicherheitshinweise
- **TRANSFORMATIONSPLAN.md** – Phase 4 Sicherheit & Stabilität
