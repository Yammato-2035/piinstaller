# Update-Center (Expertenmodul)

Zweck, Prüfungen, wann ein DEB-Build gesperrt ist, Ablauf und maßgebliche Dateien.

---

## Zweck

Das Update-Center erweitert die Seite **PI-Installer Update** um ein Experten-/Developer-Modul. Es ermöglicht:

- Kompatibilität vor einem DEB-Build zu prüfen (Linux/Pi OS, Abhängigkeiten, Versionskonsistenz, Packaging).
- **DEB-Build nur freizugeben**, wenn diese Prüfung bestanden ist (keine Blocker).
- Den letzten Prüf- und Build-Status sowie Blocker/Warnungen in der UI anzuzeigen.

Es werden **keine** neuen Endnutzer-Funktionen eingeführt; das Modul dient der kontrollierten Vorbereitung und Freigabe von DEB-Updates durch Entwickler.

---

## Was geprüft wird

- **Systembasis (Regel A):** `/etc/os-release` – nur Debian/Raspberry Pi OS (bzw. raspbian/rpi) gelten als unterstützt.
- **Abhängigkeiten (Regel B):** Python mind. 3.9; Node (empfohlen 18+) für Frontend-Build.
- **Versionskonsistenz (Regel C):** `VERSION`, `config/version.json`, `frontend/package.json`, erste Zeile `debian/changelog` müssen konsistent sein (kanonische Version aus `config/version.json` oder `VERSION`).
- **Packaging (Regel E):** Verzeichnis `debian/` mit `control` und `rules`, Skript `scripts/build-deb.sh` vorhanden.

Details: `docs/review/security/update_center_gate.md`.

---

## Wann ein DEB-Build gesperrt ist

- Sobald **mindestens ein Blocker** aus der Kompatibilitätsprüfung vorliegt (z. B. unbekanntes OS, fehlende Python-Version, Versionskonflikt, fehlende debian-Struktur).
- Das Backend antwortet auf `POST /api/update-center/build-deb` mit **400** und der Liste der Blocker, wenn `ready_for_deb_release` false ist.
- Die UI zeigt „DEB-Update gesperrt“ und listet die Blocker; der Button „DEB bauen“ ist deaktiviert.

---

## Kompatibilität erneut prüfen

- In der Seite **PI-Installer Update** auf **„Kompatibilität prüfen“** klicken.
- Backend: `POST /api/update-center/check-compatibility`. Das Ergebnis wird in der History gespeichert und in der UI (Release-Freigabe, Blocker, Warnungen) angezeigt.
- Nach Behebung der Blocker (z. B. Versionsangleichung, OS-Wechsel) erneut prüfen; bei „Release-Freigabe: freigegeben“ kann **DEB bauen** ausgeführt werden.

---

## Build auslösen

- Nur wenn **Release-Freigabe: freigegeben** (keine Blocker):
  - Button **„DEB bauen“** klicken.
  - Backend führt `scripts/build-deb.sh` im Repository-Root aus (Timeout 10 Min).
  - Ergebnis: Erfolg oder Fehler (stdout/stderr) in der Antwort; Eintrag in der History.

---

## Blocker zuerst beheben

Typische Blocker und Maßnahmen:

| Blocker | Maßnahme |
|--------|----------|
| Unbekanntes OS | Nur Debian/Raspberry Pi OS werden unterstützt; Zielsystem anpassen oder Gate-Dokumentation prüfen. |
| Python &lt; 3.9 | Python aktualisieren oder in unterstütztem Bereich entwickeln. |
| Node fehlt / &lt; 18 | Node installieren bzw. aktualisieren (empfohlen für Frontend-Build). |
| Versionskonflikt | `config/version.json`, `VERSION`, `frontend/package.json` und ggf. erste Zeile `debian/changelog` angleichen. |
| debian/ oder build-deb.sh fehlt | Repository-Struktur ergänzen (debian/, scripts/build-deb.sh). |

---

## Maßgebliche Dateien und Versionen

- **Version (kanonisch):** `config/version.json` → Feld `version`; Fallback: Datei `VERSION`.
- **Weitere Versionen:** `frontend/package.json` → `version`; `debian/changelog` → erste Zeile Format `pi-installer (X.Y.Z-N) ...`.
- **Gate-Logik:** `backend/update_center.py`.
- **API:** `backend/app.py` – Routen `/api/update-center/status`, `check-compatibility`, `release-readiness`, `build-deb`, `history`.
- **UI:** `frontend/src/pages/PiInstallerUpdate.tsx`.
- **Build:** `scripts/build-deb.sh` (wird vom Backend nur bei Freigabe aufgerufen).
- **History:** `logs/update_center_history.json` (im Repository-Root).
