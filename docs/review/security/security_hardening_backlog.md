# Security-Hardening-Backlog (nach Priorität)

_P1 = sofort, P2 = wichtig, P3 = später._

---

## P1 – Sofort

| ID | Maßnahme | Bezug | Status |
|----|----------|-------|--------|
| P1-1 | Update-Center mit Kompatibilitäts-Gate implementieren; DEB-Build/Deploy nur bei bestandenem Gate erlauben | R1, Phase 5/6 | In Umsetzung |
| P1-2 | Experten-/Developer-Update-Seite erweitern: Anzeige Blocker, „DEB-Update gesperrt“, Freigabe-Status | Phase 5 | In Umsetzung |

---

## P2 – Wichtig

| ID | Maßnahme | Bezug | Status |
|----|----------|-------|--------|
| P2-1 | Firewall-Regeln strikt validieren (Port, CIDR, Aktion) | Y2 | Offen |
| P2-2 | Backup/NAS: Pfad-Whitelist und realpath; keine Credentials in Logs | Y4, Y5 | Offen |
| P2-3 | Username-Validierung (Whitelist Zeichen, Länge); optional Passwortstärke | Y3 | Offen |
| P2-4 | DSI/Radio: URL- und Pfad-Validierung für Streams und Icons | Y7 | Offen |
| P2-5 | Logs-API: Sicherstellen, dass Pfad nur aus Konfiguration, nicht aus Request | Y8 | Offen |
| P2-6 | Remote: Audit-Log für Remote-Aktionen; strikte Aktionen-Whitelist | Y9 | Offen |

---

## P3 – Später

| ID | Maßnahme | Bezug | Status |
|----|----------|-------|--------|
| P3-1 | Alle verbleibenden run_command/shell-Art-Aufrufe auf Listen umstellen oder dokumentieren | Y1 | Teilweise |
| P3-2 | WebserverSetup: Konfig nur aus Template/Whitelist | Y6 | Offen |
| P3-3 | ControlCenter: WPA-Passphrase nicht loggen; Befehle aus Listen | Y10 | Offen |
| P3-4 | InstallationWizard: Payload-Validierung und Whitelist für Install-Start | Y11 | Offen |
| P3-5 | Security-Audit-Log für Firewall- und Benutzer-Änderungen | Y2, Y3 | Offen |
