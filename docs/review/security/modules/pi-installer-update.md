# Security Review: PiInstallerUpdate (Self-Update)

## Kurzbeschreibung

Seite "PI-Installer Update": Anzeige Quelle vs. /opt-Installation, Button "Auf /opt installieren". Backend: /api/self-update/status, /api/self-update/install (POST). Führt deploy-to-opt.sh mit sudo aus – kein Kompatibilitäts-Gate, kein Build-Gate.

## Angriffsfläche

- API: GET status (informativ), POST install (führt Deploy aus).
- Eingaben: Keine Nutzer-Parameter für install; Repo-Pfad aus Backend (Path(__file__).parent.parent).
- Kritische Aktion: Ausführung von scripts/deploy-to-opt.sh mit sudo.

## Schwachstellen

1. **Kein Release-Gate:** Deploy kann ausgeführt werden, ohne dass Kompatibilität (OS, Python, Node, Paketstände, Versionskonsistenz) geprüft wurde – Risiko inkonsistenter oder inkompatibler Installation.
2. **Keine Blocker-Anzeige:** Nutzer sieht nicht, ob z. B. Abhängigkeiten fehlen oder Versionskonflikte bestehen.
3. **Sichtbarkeit:** Eintrag unter "advanced", nicht developerOnly – alle fortgeschrittenen Nutzer können Deploy auslösen.
4. **Audit:** Kein expliziter Eintrag, wer wann Deploy ausgelöst hat.

## Empfohlene Maßnahmen

- Kompatibilitäts-Gate vor Build/Deploy: Prüfung OS (e.g. /etc/os-release), Python/Node, Paketstände, debian/, Versionskonsistenz; ready_for_deb_release nur bei bestandenem Gate.
- Backend: Neue Endpunkte z. B. /api/update-center/check-compatibility, /api/update-center/build-deb (nur wenn keine Blocker), /api/update-center/release-readiness, /api/update-center/history.
- Frontend: Update-Seite erweitern – Anzeige Kompatibilitätsstatus, Blocker, "DEB-Update gesperrt" / "Freigabe erst nach erfolgreichem Kompatibilitätscheck"; build-deb nur freigeben wenn ready.
- Optional: PiInstallerUpdate nur für experienceLevel === 'developer' sichtbar oder kritische Aktionen (Build/Deploy) nur dann.

## Ampelstatus

**GELB** (ohne Gate); nach Umsetzung Gate und Freigabe-Logik **GRÜN**. Kein klassischer ROT (keine direkte Code-Injection), aber Release-Qualität/Risiko.

## Betroffene Dateien

- backend/app.py: /api/self-update/status, /api/self-update/install.
- frontend/src/pages/PiInstallerUpdate.tsx.
- scripts/deploy-to-opt.sh.
