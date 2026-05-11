# Technische Härtung – dokumentierte Änderungen

_Pro Änderung: Datei, alte Schwäche, neue Absicherung, Nebenwirkungsprüfung. Bestehende Härtung aus security_hardening_report.md referenziert._

---

## Bereits umgesetzte Härtung (Referenz)

Siehe **docs/review/security_hardening_report.md**. Kurzüberblick:

| Datei | Alte Schwäche | Neue Absicherung | Nebenwirkung |
|-------|----------------|------------------|--------------|
| scripts/start-backend.sh | Backend an 0.0.0.0 | BIND_HOST 127.0.0.1, LAN nur mit ALLOW_REMOTE_ACCESS | Remote-Zugriff nur mit ENV |
| docker-compose.yml | Backend ports auf Host | Backend nur expose | Host-Zugriff nur mit manueller ports-Konfiguration |
| pi-installer-backend.service / pi-installer.service | Weniger Einschränkung | ProtectHome, PrivateDevices, RestrictAddressFamilies, ReadWritePaths, etc. | Bei INSTALL_DIR unter /home: ProtectHome=no setzen |
| backend/app.py | Host-Header, Shell-Aufrufe | TrustedHostMiddleware, CSP, Permissions-Policy, HSTS; Listen-Aufrufe wo umgesetzt | – |
| backend/requirements.txt, Dockerfile | – | Versionsbereiche, Supply-Chain-Kommentar | – |
| .github/workflows/security.yml | – | pip-audit, npm audit, Semgrep, Gitleaks | – |
| SECURITY.md | – | Threat Model, Ports, Security Reporting | – |

---

## Im Rahmen dieses Security-Reviews (Phase 4 / 5 / 6)

| Datei | Alte Schwäche | Neue Absicherung | Nebenwirkungsprüfung |
|-------|----------------|------------------|----------------------|
| backend/update_center.py (neu) | – | Kompatibilitäts-Gate (Regeln A–E); keine Ausführung von Build ohne bestandenes Gate | Nur Lese-/Prüf-Logik; Build wird in app.py gesteuert |
| backend/app.py | Self-Update/DEB ohne Gate | Neue Routen /api/update-center/*; build-deb nur wenn update_center.ready_for_deb_release | Bestehende /api/self-update/* unverändert; Deploy weiterhin separat (nur mit Gate-Empfehlung im Frontend) |
| frontend/src/pages/PiInstallerUpdate.tsx | Kein Gate, keine Blocker-Anzeige | Anzeige Kompatibilitätsstatus, Blocker, „DEB-Update gesperrt“, Freigabe-Status; Build-Button nur bei Freigabe | Normale Nutzer sehen Sperre bis Kompatibilität bestanden |
| docs/review/security/update_center_gate.md | – | Dokumentation der Gate-Regeln | – |
| docs/review/security/expert_module_access.md | – | Dokumentation Sichtbarkeit Experten/Developer | – |

Weitere technische Härtungen (Y1–Y11) sind im Backlog erfasst; Umsetzung je nach Priorität (P2/P3).
