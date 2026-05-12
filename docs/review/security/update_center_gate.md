# Update-Center: Kompatibilitäts-Gate

Das DEB-Build und die Freigabe werden erst nach bestandenem Kompatibilitäts-Gate erlaubt.

---

## Regeln (A–E)

### REGEL A – Systembasis

- Unterstütztes Linux / Debian / Raspberry Pi OS wird über `/etc/os-release` erkannt.
- Erlaubte IDs: `debian`, `raspbian`, `rpi` (inkl. ID_LIKE-Ableitung).
- Unbekannte oder ungetestete Zielbasis führt zu einem **Blocker** (keine Freigabe).

### REGEL B – Abhängigkeiten

- **Python:** Mindestversion 3.9 (aktueller Prozess).
- **Node/npm:** Vorhanden und empfohlen Version 18+ für Frontend-Build; fehlt Node oder Version &lt; 18 → Blocker bzw. Warnung (Build ohne Frontend möglich).
- Nötige Systempakete für Build/Install (z. B. debhelper, rsync) werden über vorhandene debian/control abgeleitet; keine automatische apt-Prüfung im Gate.

### REGEL C – Versionskonsistenz

- Keine widersprüchlichen Versionsdateien.
- Geprüft: `VERSION`, `config/version.json`, `frontend/package.json`, erste Zeile `debian/changelog`.
- Kanonische Version: `config/version.json` → fallback `VERSION`.
- Abweichungen in anderen Dateien → **Blocker**.

### REGEL D – Sicherheitsstatus

- Keine offenen ROT-Punkte, die Release-Blocker sind.
- Aktuell: Aus Kompatibilitätsprüfung abgeleitet (alle Regeln A–C und E bestanden = D erfüllt).
- GELB darf mit ausdrücklicher Anzeige (Warnungen) bestehen bleiben; Build bleibt erlaubt wenn keine Blocker.

### REGEL E – Packaging

- `debian/` Struktur vorhanden: Verzeichnis, `control`, `rules`.
- Build-Skript `scripts/build-deb.sh` vorhanden.
- Fehlende Struktur → **Blocker**.

---

## Ablauf

1. **Kompatibilität prüfen:** `POST /api/update-center/check-compatibility` führt alle Prüfungen aus (kein Build). Ergebnis: `checks_passed`, `blockers`, `warnings`, `ready_for_deb_release`.
2. **Release-Readiness:** `GET /api/update-center/release-readiness` liefert den aktuellen Freigabestatus (auf Basis der letzten Prüfung bzw. Live-Check).
3. **DEB bauen:** `POST /api/update-center/build-deb` führt `scripts/build-deb.sh` **nur** aus, wenn `ready_for_deb_release === true`. Andernfalls: 400 mit Blocker-Liste.
4. **Deploy auf /opt:** Unverändert über `POST /api/self-update/install` (Deploy-Skript). Empfohlen: Nur ausführen, wenn zuvor Kompatibilität bestanden hat (Frontend zeigt Gate-Status).

---

## Implementierung

- **Backend:** `backend/update_center.py` (Prüflogik), Routen in `backend/app.py` unter `/api/update-center/*`.
- **History:** `logs/update_center_history.json` (letzte Prüf-/Build-Läufe).
- **Frontend:** `frontend/src/pages/PiInstallerUpdate.tsx` – Expertenmodul mit Ampel, Blocker-Anzeige, Buttons „Kompatibilität prüfen“ und „DEB bauen“ (nur bei Freigabe aktiv).
