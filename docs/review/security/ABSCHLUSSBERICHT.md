# Security-Review – Abschlussbericht

_Stand: Vollständiges modulares Security-Review inkl. Update-Center und Kompatibilitäts-Gate._

---

## 1. Geänderte Dateien

| Datei | Änderung |
|-------|----------|
| backend/app.py | Import update_center; neue Routen /api/update-center/status, check-compatibility (POST), release-readiness (GET), build-deb (POST), history (GET). |
| frontend/src/pages/PiInstallerUpdate.tsx | Erweiterung um Expertenmodul: Update-Center-Status, Release-Readiness, Kompatibilitätsprüfung, DEB-Build-Button, Blocker-Anzeige, Ampel, „DEB-Update gesperrt“. |

---

## 2. Neu erstellte Dateien

| Datei | Inhalt |
|-------|--------|
| docs/review/security/module_inventory.md | Modulinventur: Hauptmodule, Backend-Endpunkte, Befehle/sudo, Angriffsfläche. |
| docs/review/security/module_security_matrix.md | Sicherheits-Matrix (Modul, Bereich, Eingaben, Aktionen, Rechte, Exponierung, Schutz, Härtung, Ampel, Release-Blocker). |
| docs/review/security/security_checklist_ampel.md | Schwachstellen-Checkliste A (ROT), B (GELB), C (GRÜN) mit ID, Modul, Risiko, Maßnahme, Status, Release-Blocker. |
| docs/review/security/security_hardening_backlog.md | Backlog P1/P2/P3 für Härtungsmaßnahmen. |
| docs/review/security/hardening_changes.md | Dokumentation technischer Härtung (bestehend + Update-Center). |
| docs/review/security/update_center_gate.md | Gate-Regeln A–E, Ablauf, Implementierungshinweise. |
| docs/review/security/expert_module_access.md | Rollen/Sichtbarkeit Expertenbereich, Update-Center, Optionen developerOnly. |
| docs/review/security/modules/*.md | Pro Modul Security-Review (Kurzbeschreibung, Angriffsfläche, Schwachstellen, Maßnahmen, Ampel, Code-Stellen). |
| backend/update_center.py | Kompatibilitätsprüfung (OS, Python, Node, Versionskonsistenz, debian/), History, keine Build-Ausführung (nur Logik). |
| docs/developer/update-center.md | Developer-Doku: Zweck, Prüfungen, Sperre, Ablauf, Blocker beheben, maßgebliche Dateien. |
| docs/review/security/ABSCHLUSSBERICHT.md | Dieser Bericht. |

---

## 3. ROT / GELB / GRÜN (Checkliste)

- **ROT:** 1 Punkt (R1 – Gate für DEB/Release). **Umgesetzt:** Update-Center mit Kompatibilitätsprüfung; build-deb nur bei ready_for_deb_release; UI zeigt Blocker und „DEB-Update gesperrt“.
- **GELB:** 11 Punkte (Y1–Y11). Überwiegend **nur dokumentiert** (Backlog P2/P3); keine neuen Produktfunktionen, keine blinden Refactorings.
- **GRÜN:** 14 Punkte (G1–G14). Bestätigt als ausreichend abgesichert bzw. Restverbesserungen.

---

## 4. Direkt umgesetzt

- **Update-Center Backend:** Kompatibilitätsprüfung (Regeln A–E), Endpunkte status, check-compatibility, release-readiness, build-deb (nur bei Freigabe), history.
- **Update-Center Frontend:** Expertenmodul in PiInstallerUpdate: Anzeige installierte/Quell-Version, letzter Check/Build, Ampel, Release-Freigabe gesperrt/freigegeben, Blocker-Liste, Buttons „Kompatibilität prüfen“ und „DEB bauen“ (nur bei Freigabe).
- **Gate:** build-deb verweigert mit 400 und Blocker-Liste, wenn ready_for_deb_release false ist.
- **Dokumentation:** Alle Phasen (Inventur, Matrix, Modul-Reviews, Checkliste, Backlog, Gate, Experten-Zugriff, Developer Update-Center) dokumentiert.

---

## 5. Bewusst nur dokumentiert

- Firewall-Regel-Validierung (Y2), Pfad-Whitelist Backup/NAS (Y4, Y5), Username/Passwortstärke (Y3), DSI/Radio URL-Pfad (Y7), Logs-API-Pfad (Y8), Remote-Audit (Y9), ControlCenter WPA (Y10), InstallationWizard Payload (Y11), verbleibende shell-Aufrufe (Y1). Siehe security_hardening_backlog.md (P2/P3).
- README/SECURITY.md wurden nicht geändert (laut Vorgabe nur bei Bedarf; bestehende SECURITY.md und security_hardening_report.md bleiben Referenz).

---

## 6. Offene Risiken

- GELB-Punkte bleiben als Restrisiko bis zur Umsetzung im Backlog (Pfad-Validierung, Firewall-Validierung, Credential-Redaction, etc.).
- Update-Center ist für alle „advanced“ Nutzer sichtbar; bei Bedarf auf developerOnly umstellbar (siehe expert_module_access.md).
- Keine Authentifizierung der API (LAN/VPN-Modell); unverändert.

---

## 7. Gesamtbewertung Sicherheitsniveau

- **Vor dem Review:** Bereits Härtung (127.0.0.1, TrustedHost, systemd, CORS, Sudo-Store) vorhanden (security_hardening_report.md).
- **Nach dem Review:** Modulübersicht und Bewertung aller Hauptmodule; klare Ampel-Checkliste; **Release-relevantes Risiko (R1)** durch Update-Center und Kompatibilitäts-Gate adressiert. DEB-Build ist nur nach bestandener Prüfung möglich; Blocker werden angezeigt und blockieren die Freigabe.
- **Einschätzung:** Für den vorgesehenen Einsatz (LAN/VPN, Entwickler-Update-Workflow) ist das Sicherheitsniveau **erhöht**; offene GELB-Punkte sind priorisiert und dokumentiert.
