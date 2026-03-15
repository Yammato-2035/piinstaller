# Sicherheits- und Härtungsbericht (Phasen 1–7)

_Stand: Nach Umsetzung der sieben Phasen. Keine neuen Funktionen; ausschließlich sicherheitsrelevante Änderungen und Dokumentation._

---

## 1. Prüfung: Sind die Sicherheitsmaßnahmen korrekt umgesetzt?

| Phase | Maßnahme | Status |
|-------|----------|--------|
| 1 | Backend standardmäßig 127.0.0.1 in start-backend.sh | ✅ |
| 1 | LAN optional über ALLOW_REMOTE_ACCESS | ✅ |
| 1 | docker-compose: Backend nur expose, kein ports | ✅ |
| 2 | systemd: Zusätzliche Härtungsoptionen (ProtectHome, PrivateDevices, RestrictAddressFamilies, etc.) | ✅ |
| 2 | ReadWritePaths mit {{INSTALL_DIR}} | ✅ |
| 3 | hostname/hostname -I ohne shell=True | ✅ |
| 3 | Temperatur-Lesen via Path statt subprocess | ✅ |
| 3 | curl PUT ohne shell (Listen-Aufruf) | ✅ |
| 3 | Verbleibende shell-Aufrufe mit SECURITY NOTE dokumentiert | ✅ |
| 4 | TrustedHostMiddleware, erweiterte Security-Header (CSP, Permissions-Policy, HSTS bei HTTPS) | ✅ |
| 5 | requirements.txt: Versionsbereiche + Supply-Chain-Kommentar; Dockerfile-Kommentar | ✅ |
| 6 | security.yml: pip-audit, npm audit, Semgrep, Gitleaks (nur Reports) | ✅ |
| 7 | SECURITY.md: Threat Model, Ports/Dienste, Security Reporting | ✅ |

---

## 2. Prüfung: Neue Fehler?

- **Linter:** Keine Meldungen in backend/app.py.
- **Mögliche Nebenwirkungen:**
  - **ProtectHome=yes:** Wenn INSTALL_DIR unter /home liegt (z. B. /home/pi/piinstaller), startet der Service nicht korrekt. In den Service-Dateien steht der Hinweis: „Bei INSTALL_DIR unter /home: ProtectHome=no setzen.“
  - **Backend nur 127.0.0.1:** Wer das Backend per systemd mit start-backend.sh startet und aus dem LAN aufrufen will, muss `ALLOW_REMOTE_ACCESS=true` (z. B. in der systemd-Umgebung) setzen.
  - **TrustedHostMiddleware:** Anfragen mit unbekanntem Host-Header erhalten 400. Bei Reverse-Proxy den Proxy-Host in PI_INSTALLER_ALLOWED_HOSTS aufnehmen (bei ALLOW_REMOTE_ACCESS=true).
  - **Docker:** Backend nur „expose“ – vom Host-Browser aus ist das Backend nicht erreichbar, sofern nicht wieder `ports: - "8000:8000"` gesetzt wird (laut Kommentar im docker-compose).

---

## 3. Prüfung: Bestehende Funktionen verändert?

- **Nein**, außer wo es sicherheitsrelevant war:
  - Standard-Bind-Adresse des Backends ist jetzt 127.0.0.1 (vorher 0.0.0.0 in start-backend.sh).
  - Docker: Backend-Port nicht mehr auf den Host gemappt; Frontend unverändert erreichbar.
  - Keine Änderung an fachlicher Logik (Endpoints, Sudo-Store, CORS-Logik, etc.).

---

## 4. Alle Änderungen nach Priorität

### A = Kritische Sicherheitsverbesserung

- Backend standardmäßig nur 127.0.0.1 (start-backend.sh).
- TrustedHostMiddleware gegen Host-Header-Spoofing.
- systemd: RestrictAddressFamilies, SystemCallFilter, CapabilityBoundingSet=, NoNewPrivileges (bereits vorher, beibehalten).

### B = Wichtige Härtungsmaßnahme

- systemd: ProtectHome, PrivateDevices, ProtectKernelTunables, ProtectControlGroups, ProtectKernelLogs, LockPersonality, RestrictSUIDSGID, ReadWritePaths.
- Erweiterte Security-Header (CSP, Permissions-Policy, HSTS bei HTTPS).
- Shell-Aufrufe: hostname, Temperatur-Lesen, curl PUT ohne shell; restliche Aufrufe mit SECURITY NOTE dokumentiert.
- docker-compose: Backend nur expose.

### C = Dokumentation / Prozess

- SECURITY.md: Threat Model, Ports/Dienste, Security Reporting.
- requirements.txt / Dockerfile: Supply-Chain-Hinweise.
- GitHub-Workflow security.yml (pip-audit, npm audit, Semgrep, Secret-Scan).

---

## 5. Geänderte Dateien (Übersicht)

| Datei | Phase | Inhalt |
|-------|--------|--------|
| scripts/start-backend.sh | 1 | BIND_HOST 127.0.0.1 default, ALLOW_REMOTE_ACCESS für 0.0.0.0 |
| docker-compose.yml | 1 | Backend: expose statt ports; Kommentar |
| pi-installer-backend.service | 2 | Zusätzliche systemd-Härtung |
| pi-installer.service | 2 | Zusätzliche systemd-Härtung |
| backend/app.py | 3, 4 | Shell-Aufrufe angepasst/dokumentiert; TrustedHost, CSP, Permissions-Policy, HSTS |
| backend/requirements.txt | 5 | Versionsbereiche (starlette, fastapi, uvicorn), Supply-Chain-Kommentar |
| Dockerfile | 5 | Kommentar Image-Pinning |
| .github/workflows/security.yml | 6 | Neu: pip-audit, npm audit, Semgrep, Gitleaks |
| SECURITY.md | 7 | Threat Model, Ports/Dienste, Security Reporting, aktualisierte Maßnahmenliste |

---

## 6. Kurze Sicherheitsbewertung nach Umsetzung

- **Netzwerk:** Backend ist standardmäßig nicht vom LAN/Internet aus erreichbar; LAN nur nach expliziter Freigabe (ALLOW_REMOTE_ACCESS). Docker-Backend ist nur im Container-Netz sichtbar.
- **Host/Header:** Unerwünschte Host-Header werden abgewiesen (TrustedHost).
- **Anwendung:** Bestehende Maßnahmen (CORS, Sudo-Verschlüsselung, Rate-Limit, Security-Header) bleiben; ergänzt um CSP, Permissions-Policy, HSTS bei HTTPS.
- **Prozess:** systemd-Services sind deutlich stärker eingegrenzt (Dateisystem, Netzwerk, Capabilities, Syscalls). Bei Installation unter /home muss ProtectHome angepasst werden.
- **Supply-Chain:** Versionsbereiche und zentrale Security-Scans (pip-audit, npm audit, Semgrep, Secret-Scan) verbessern die Überprüfbarkeit; keine automatischen Codeänderungen.
- **Dokumentation:** Threat Model und Security Reporting sind festgehalten; Betreiber und Nutzer haben eine klare Referenz für Betrieb und Meldung von Lücken.

Gesamt: Das Projekt ist für den vorgesehenen Einsatz (LAN/VPN, optional hinter Reverse-Proxy) deutlich gehärtet; direkte Internetexposition bleibt explizit nicht empfohlen und ist durch sichere Defaults und Doku eingegrenzt.
