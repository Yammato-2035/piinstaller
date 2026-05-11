# Anti Regression Rules

_Stand: 2026-03-09_

## 1. Zweck

Diese Regeln sollen verhindern, dass bekannte Fehlerklassen bei späteren Änderungen erneut ins Projekt eingebaut werden. Sie basieren auf dem System Audit Report (`docs/SYSTEM_AUDIT_REPORT.md`) und dokumentierten Fixes (`docs/review/audit_fix_log.md`).

**Kein Feature- oder Refactoring-Schritt:** Es werden ausschließlich Schutzmechanismen, Prüfregeln und Dokumentation ergänzt.

---

## 2. Bekannte Fehlerklassen

### A) Doppelte Konfigurationen

- Mehrfach gesetzte Schlüssel in verschiedenen Dateien
- Konkurrierende Default-Werte (z. B. `config.yaml` vs. `config.json`)
- Gleiche Settings in mehreren Quellen (Installer, Backend, Doku)
- Mehrfache Initialisierung derselben Option
- Konkurrierende ENV-/Datei-/Runtime-Werte (z. B. `PI_INSTALLER_DEBUG_CONFIG` vs. `PIINSTALLER_DEBUG_*`)
- Port-/Host-Annahmen an mehreren Stellen (`3000`/`3001`, `8000`)

### B) Doppelte oder parallele Funktionen

- Utilities mit gleicher Aufgabe (z. B. `_publish()` in zwei Services)
- Alte und neue Implementierung parallel
- Wrapper ohne erkennbaren Mehrwert
- Copy-Paste-Helfer in mehreren Modulen

### C) Alt-Debugging parallel zum neuen System

- `print()`/`console.*`/log-Spam im Produktivpfad
- Veraltete Debug-Flags, Dauerlogging, Debug-Polling
- Ungenutzte Diagnosepfade
- Zwei Logging-Welten nebeneinander (altes File-Log vs. `backend/debug`)

### D) Gefährliche Systemänderungen

- Änderungen an Boot-Reihenfolge
- Änderungen an Startskripten ohne vollständige Prüfung
- Änderungen an Hardware-Erkennung, Storage-, Mount-, NVMe-, SD-Logik
- Änderungen an Persistenzpfaden
- Doppelte Einträge in systemnahen Konfigurationen (Service-Templates, postinst)

### E) UI-/UX-Regressionen

- Expertenoptionen versehentlich in Basisscreens
- Unklare Vermischung von Grundlagen und Erweitert
- Alte Links/Buttons bleiben sichtbar, verweisen aber ins Leere
- Doppelte Navigation oder tote Menüeinträge
- Neue UI-Optionen zu nicht implementierten Backend-Endpunkten

### F) Tote Links und Referenzen

- API-Endpunkte im Frontend, die im Backend nicht existieren
- Asset-Pfade (Icons, Screenshots), die nicht vorhanden sind
- Externe Links, die nicht mehr gültig sind
- Doku-Pfade, die von der Runtime abweichen

---

## 3. Verbindliche Änderungsregeln

| Regel | Beschreibung |
|-------|---------------|
| Keine neue Konfiguration ohne Prüfung | Vor jedem neuen Config-Key: Suche nach bestehenden Schlüsseln in `backend/app.py`, `backend/debug/config.py`, Installer-Skripten, Doku. |
| Keine zweite Implementierung | Keine Parallelimplementierung derselben Fachlogik. Vor neuen Modulen: Prüfen, ob `backend/app.py` oder `backend/modules/*` bereits zuständig ist. |
| Kein Debug-Code außerhalb des zentralen Mechanismus | Neue Debug-Ausgaben nur über `backend/debug` (Logger, Instrumentation). Kein `print()` im Produktivpfad, kein `console.*` ohne Dev-Only-Guard. |
| Keine systemnahen Änderungen ohne Prüfung | Änderungen an Boot-, Storage-, Hardware-, Start- oder Persistenzlogik nur nach vollständiger Prüfung aller betroffenen Skripte und Services. |
| Keine neuen UI-Optionen ohne Einordnung | Jede neue UI-Option muss als „Grundlagen“ oder „Erweitert“ eingeordnet werden. Keine Expertenfunktionen in Basisscreens. |
| Keine stillen Defaults in mehreren Ebenen | Ports, Pfade, ENV-Variablen: Eine klare Source of Truth. Keine Duplikation von Default-Werten. |
| Keine toten Verweise | Neue Links, Buttons, API-Aufrufe nur, wenn das Ziel existiert. Bei geplanter Implementierung: UI klar als „nicht verfügbar“ markieren. |

---

## 4. Prüffragen vor jeder Änderung

- [ ] Existiert dafür bereits eine Funktion?
- [ ] Existiert dafür bereits ein Helper/Service?
- [ ] Existiert dafür bereits ein Config-Key oder Setting?
- [ ] Existiert dafür bereits ein Debugpfad?
- [ ] Wird bestehende Boot-/Storage-/Hardwarelogik berührt?
- [ ] Gehört die Änderung in Grundlagen oder Erweitert?
- [ ] Entsteht ein zweiter Wahrheitsort?
- [ ] Werden bestehende Pfade, Links oder Menüeinträge ungültig?

---

## 5. No-Go-Liste

- Keine doppelte Config (z. B. YAML und JSON parallel für dieselbe Domäne)
- Keine Parallelimplementierung derselben Fachlogik
- Keine Alt-Debugausgabe im Produktivpfad
- Keine systemnahen Änderungen ohne explizite Prüfung
- Keine versteckten Seiteneffekte (stille Config-Änderungen, Default-Overrides)
- Keine Navigation oder API-Aufrufe zu nicht vorhandenen Zielen

---

## 6. Minimaler Review-Prozess

Vor Änderungen:

1. Bestehende Implementierung suchen
2. Konfigurationsquelle und Default-Werte suchen
3. Debug-Anbindung prüfen (zentrales System vs. Ad-hoc)
4. Seiteneffekte auf Start-, Boot-, Storage-, Hardwarepfade prüfen
5. Erst dann ändern

---

## 7. Kritische Bereiche mit erhöhter Vorsicht

| Bereich | Ort / Datei / Modul | Warum regressionsanfällig | Typische Fehler | Was immer geprüft werden muss |
|---------|---------------------|---------------------------|-----------------|-------------------------------|
| Config-Ladepfade | `backend/app.py` `_config_path()`, `_load_or_init_config()` | Runtime liest ausschließlich `config.json`; Installer/Doku könnten wieder auf YAML wechseln | Wiederaufnahme von `config.yaml` als Quelle | Config-Pfad muss `.json` bleiben |
| Default-Werte | `backend/app.py` `_default_settings()`, `backend/debug/defaults.yaml` | Mehrfache Default-Quellen, Merge-Logik | Widersprüchliche Defaults in verschiedenen Modulen | Keine neuen Defaults ohne Prüfung bestehender |
| Start-/Init-Reihenfolge | `start-backend.sh`, `start.sh`, `pi-installer.service`, `pi-installer-backend.service` | Mehrere Service-Templates, verschiedene User/WorkingDirectory | Unterschiedliches Verhalten je Installationsweg | Keine Änderung an Startreihenfolge ohne vollständige Prüfung |
| Debug-Aktivierung | `backend/debug/config.py`, `backend/debug/debug.config.yaml` | Kommentar vs. Loader inkonsistent; ENV-Namen `PIINSTALLER_DEBUG_*` | Falsche Erwartung an Debug-Steuerung | ENV- und Pfad-Doku mit Loader abgleichen |
| Hardware-/Storage-Erkennung | `scripts/*nvme*`, `scripts/*hdmi*`, `scripts/*freenove*` | Viele ähnliche Skripte, Hardware-spezifische Workarounds | Unbeabsichtigte Seiteneffekte bei Änderungen | Keine Änderung ohne Nutzungsanalyse |
| Navigation / Routing / Menüstruktur | `frontend/src/App.tsx`, `frontend/src/pages/Documentation.tsx` | Mehrere Produkte in einer Navigation; Deep-Links | Tote Menüeinträge, falsche Ziele | Neue Einträge nur mit existierendem Ziel |
| UI-Trennung Grundlagen vs. Erweitert | `frontend/src/pages/ControlCenter.tsx`, `RaspberryPiConfig.tsx`, `BackupRestore.tsx` | Expertenoptionen neben Basisfunktionen | Fehlbedienung, Überforderung | Jede neue Option einordnen |
| API-Endpunkt-Konsistenz | `frontend/src/pages/*Setup*.tsx`, `backend/app.py` | UI kann Endpunkte aufrufen, die nicht existieren | 404, fehlende Implementierung | Kein fetch zu neuem Endpunkt ohne Backend-Implementierung |
| Sudo-/Dialog-Komponenten | `SudoPasswordDialog.tsx`, `SudoPasswordModal.tsx` | Zwei parallele Komponenten mit überlappender Verantwortung | Inkonsistente UX, doppelte Wartung | Nutzungspfad dokumentieren, keine dritte Komponente |

---

## 8. Minimale Validierung (empfohlen für später)

Falls erweitert werden soll, ohne neue Testarchitektur:

- **Config:** Prüfung, dass `_config_path()` auf `.json` endet
- **Routes:** Prüfung auf doppelte FastAPI-Routen (z. B. gleicher Pfad zweimal)
- **Debug:** Prüfung, ob Modul altes Logging statt `backend/debug` nutzt
- **Frontend:** Prüfung, ob API-Aufrufe zu dokumentierten Endpunkten führen

Aktuell ist in `backend/tests/test_anti_regression.py` eine minimale Prüfung für den Config-Pfad ergänzt.

---

## 9. Referenzen

- `docs/SYSTEM_AUDIT_REPORT.md` – Vollständiger Audit-Report
- `docs/review/audit_fix_log.md` – Protokoll der Priorität-A-Fixes
- `docs/development/change_checklist.md` – Operative Checkliste vor Änderungen
