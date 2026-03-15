# Schwachstellen-Checkliste mit Ampelbewertung

_Stand: Nach modulweisem Security Review. Jeder Punkt mit ID, Modul, Risiko, Maßnahme, Umsetzungsstatus, Release-Blocker._

---

## A. ROT – Kritische Schwachstellen / Release-Blocker

| ID | Modul | Schwachstelle | Risiko | Empfohlene Maßnahme | Umsetzungsstatus | Release-Blocker |
|----|--------|----------------|--------|---------------------|------------------|-----------------|
| R1 | PiInstallerUpdate / Self-Update | DEB-Build/Deploy ohne Kompatibilitäts-Gate auslösbar | Inkompatibles Update, fehlende Abhängigkeiten, Versionsbrüche | Update-Center mit Kompatibilitätsprüfung; Build/Deploy nur bei bestandenem Gate | Umgesetzt (Update-Center + Gate) | ja (erledigt) |

_Hinweis: Keine weiteren ROT-Punkte (z. B. direkte RCE oder Path-Traversal mit Nachweis) identifiziert. R1 wird durch Implementierung des Update-Centers und Gates behoben._

---

## B. GELB – Wichtige Schwachstellen / zeitnah beheben

| ID | Modul | Schwachstelle | Risiko | Empfohlene Maßnahme | Umsetzungsstatus | Release-Blocker |
|----|--------|----------------|--------|---------------------|------------------|-----------------|
| Y1 | Backend Core | Verbleibende shell-ähnliche/subprocess-Aufrufe mit String-Konkatenation | Command Injection bei Fehlkonfiguration | Alle Aufrufe auf Listen umstellen oder shlex.quote; keine Nutzerdaten in Strings | Teilweise umgesetzt (dokumentiert) | nein |
| Y2 | SecuritySetup | Firewall-Regeln nicht strikt validiert | Ungültige/gefährliche UFW-Regeln | Port 1–65535, CIDR-Format, Whitelist Aktionen | Offen | nein |
| Y3 | UserManagement | Username/Passwortstärke, Rate-Limit create/delete | Brute-Force, schwache Accounts | Username-Whitelist, optional Passwortstärke, Rate-Limit | Teilweise (Rate-Limit sudo) | nein |
| Y4 | BackupRestore | Pfad- und Credential-Handling | Path Traversal, Credential-Leak in Logs | Pfad-Whitelist/realpath; Redaction Credentials | Offen | nein |
| Y5 | NASSetup | Pfade aus Request | Path Traversal | Strikte Pfad-Validierung, Whitelist | Offen | nein |
| Y6 | WebserverSetup | Konfig-Inhalte aus Request | Injection in Nginx/Apache-Config | Template/Whitelist, keine Roh-Bodies | Offen | nein |
| Y7 | DSI/Radio | Stream-URLs, Icon-Pfade | SSRF, Path Traversal | URL- und Pfad-Validierung | Offen | nein |
| Y8 | Logs API | Pfad aus Konfiguration vs. Request | Path Traversal wenn Pfad aus Request | Fester Log-Pfad, kein User-Parameter | Prüfen | nein |
| Y9 | Remote | Aktionen/Parameter von Remote | Unberechtigte oder gefährliche Aktionen | Strikte Permission-Checks, Whitelist Aktionen, Audit | Teilweise (Permissions) | nein |
| Y10 | ControlCenter | WLAN-Passphrase, Befehle | Logging/Injection | Keine Passphrase in Logs; Listen-Argumente | Offen | nein |
| Y11 | InstallationWizard | Payload in Install-Start | Command Injection | Whitelist Optionen, Listen für subprocess | Prüfen | nein |

---

## C. GRÜN – Ausreichend abgesichert / Restverbesserungen

| ID | Modul | Bewertung | Release-Blocker |
|----|--------|-----------|-----------------|
| G1 | Dashboard | Nur Lese-API, keine sensiblen Daten | nein |
| G2 | MonitoringDashboard | Geringe kritische Oberfläche, Konfig-Validierung empfohlen | nein |
| G3 | PeripheryScan | Nur Scan, keine Schreib-/Install-Aktionen | nein |
| G4 | AppStore | App-Whitelist (APPS_CATALOG), keine beliebigen IDs | nein |
| G5 | Documentation | Keine Backend-Aktionen | nein |
| G6 | SettingsPage | Keine privilegierten Aktionen | nein |
| G7 | SudoPasswordDialog / Store | Verschlüsselung, TTL, Rate-Limit | nein |
| G8 | DevelopmentEnv | developerOnly, Paket-Validierung empfohlen | nein |
| G9 | MailServerSetup | developerOnly | nein |
| G10 | Debian Packaging | Reproduzierbar; Versionskonsistenz über Gate | nein |
| G11 | systemd Services | Härtung (ProtectHome, RestrictAddressFamilies, etc.) umgesetzt | nein |
| G12 | RaspberryPiConfig | Nur auf Pi, whitelistete Konfiguration | nein |
| G13 | FirstRunWizard | Keine privilegierten Aktionen | nein |
| G14 | TFTPage | Anzeige/Konfig, siehe DSI | nein |

---

## Zählung (für Lagemeldung)

- **ROT:** 1 (R1 – Gate für Update/Release).
- **GELB:** 11 (Y1–Y11).
- **GRÜN:** 14 (G1–G14).

Nach Umsetzung von Update-Center und Kompatibilitäts-Gate: R1 erledigt → 0 ROT, GELB/GRÜN unverändert.
