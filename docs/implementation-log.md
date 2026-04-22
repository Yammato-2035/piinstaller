# Testmatrix – Backup / Restore

## Legende
- B = Bestanden
- BE = Bestanden mit Einschränkung
- NB = Nicht bestanden
- NT = Nicht testbar

| ID | Bereich | Testfall | Erwartung | Status | Beobachtung | Risiko | Maßnahme |
|----|---------|----------|-----------|--------|-------------|--------|----------|
| BR-001 | Backup | Vollbackup kann gestartet werden | Job startet sauber, Status sichtbar |  |  |  |  |
| BR-002 | Backup | Vollbackup endet erfolgreich | Abschlussstatus korrekt, Datei vorhanden |  |  |  |  |
| BR-003 | Backup | Backup bei ungültigem Zielpfad | verständliche Fehlermeldung, kein Crash |  |  |  |  |
| BR-004 | Backup | Backup bei fehlendem Speicherplatz | sauberer Abbruch, klare Meldung |  |  |  |  |
| BR-005 | Backup | Backup bei fehlenden Rechten | klare Fehlermeldung, kein stilles Scheitern |  |  |  |  |
| BR-006 | Backup | Abbruch eines laufenden Backup-Jobs | Abbruchzustand konsistent |  |  |  |  |
| BR-007 | Backup | Mehrfachstart / parallele Jobs | definierte Sperre oder klare Regel |  |  |  |  |

| BR-008 | Inkrementell | Inkrementelles Backup ohne Basisbackup | klarer Fehler oder definierter Fallback |  |  |  |  |
| BR-009 | Inkrementell | Inkrementelles Backup mit gültiger Basis | logisch korrekt erzeugt |  |  |  |  |
| BR-010 | Inkrementell | Mehrere inkrementelle Sicherungen in Folge | Kette nachvollziehbar |  |  |  |  |
| BR-011 | Inkrementell | Verifikation einer inkrementellen Kette | Grenzen klar dokumentiert |  |  |  |  |

| BR-012 | Verschlüsselung | Verschlüsseltes Backup kann erstellt werden | Datei wird erzeugt, Status korrekt |  |  |  |  |
| BR-013 | Verschlüsselung | Backup ohne Passwort trotz aktivierter Verschlüsselung | sauber blockiert oder klare Regel |  |  |  |  |
| BR-014 | Verschlüsselung | Falsches Passwort beim Restore | klarer Fehler, kein stilles Scheitern |  |  |  |  |
| BR-015 | Verschlüsselung | Verifikation verschlüsselter Backups | tatsächlicher Umfang der Prüfung klar benannt |  |  |  |  |
| BR-016 | Verschlüsselung | Passwort-/Schlüsselhandling in Logs | keine sensiblen Daten in Logs |  |  |  |  |

| BR-017 | Restore | Restore-Liste zeigt gültige Backups korrekt | Metadaten nachvollziehbar |  |  |  |  |
| BR-018 | Restore | Restore mit normalem Backup | definierter Erfolg oder klarer Fehler |  |  |  |  |
| BR-019 | Restore | Restore mit verschlüsseltem Backup | definierter Erfolg oder klarer Fehler |  |  |  |  |
| BR-020 | Restore | Restore mit beschädigtem Backup | sicherer Abbruch, klare Fehlermeldung |  |  |  |  |
| BR-021 | Restore | Restore auf Root-Dateisystem | Risiko klar sichtbar, Schutzmechanismus vorhanden |  |  |  |  |
| BR-022 | Restore | Restore ohne Sicherheitsbestätigung | muss blockiert oder bestätigt werden |  |  |  |  |
| BR-023 | Restore | Restore-Zielpfad unklar oder ungültig | kein stilles Überschreiben |  |  |  |  |
| BR-024 | Restore | Restore kann nicht vollständig ausgeführt werden | sauberer Fehlerzustand |  |  |  |  |

| BR-025 | Verifikation | Normales Backup wird verifiziert | Ergebnis nachvollziehbar |  |  |  |  |
| BR-026 | Verifikation | Beschädigtes Archiv wird erkannt | Fehler wird erkannt |  |  |  |  |
| BR-027 | Verifikation | Leere/zu kleine Backup-Datei | Fehler oder Warnung |  |  |  |  |
| BR-028 | Verifikation | Verschlüsselte Datei nur oberflächlich prüfbar | das wird offen benannt |  |  |  |  |

| BR-029 | UI/UX | UI unterscheidet Info/Warnung/Fehler | klar lesbar und konsistent |  |  |  |  |
| BR-030 | UI/UX | UI zeigt riskante Restore-Hinweise deutlich | Warnung nicht versteckt |  |  |  |  |
| BR-031 | UI/UX | UI-Status stimmt mit Backend-Status überein | kein Widerspruch |  |  |  |  |
| BR-032 | UI/UX | Fehlermeldungen sind verständlich | kein roher Technikmüll für Anfänger |  |  |  |  |

| BR-033 | Logging | Relevante Fehler werden geloggt | Log nutzbar für Diagnose |  |  |  |  |
| BR-034 | Logging | Logs enthalten keine Passwörter/Secrets | keine Leaks |  |  |  |  |
| BR-035 | Logging | Logs liefern genug Kontext für FAQ/Diagnose | Ursache und Maßnahme ableitbar |  |  |  |  |

| BR-036 | Diagnosefähigkeit | Fehlerbilder lassen sich in diagnostics-notes überführen | ja, strukturiert |  |  |  |  |
| BR-037 | Doku | implementation-log wurde ergänzt | vollständig |  |  |  |  |
| BR-038 | Doku | faq-source-notes wurde ergänzt | relevante Erkenntnisse enthalten |  |  |  |  |
| BR-039 | Doku | diagnostics-notes wurde ergänzt | verwertbare Checks abgeleitet |  |  |  |  |
# Implementation Log – Branding & Panda Helper

## Branding, Logo & Helper Figure

- SetupHelfer Hauptlogo identifiziert und für das UI vereinheitlicht:
  - Primärlogo: `frontend/public/assets/branding/logo/logo-main.svg`
  - Varianten: `logo-dark.svg`, `logo-flat.svg` (Filter auf Basis von `logo-main.svg`)
- Header/Sidebar:
  - Logo im linken oberen Bereich der Sidebar eingebunden (Tauri + Web, da aus `public/assets` geladen).
  - Panda bleibt ergänzendes Maskottchen, nicht Ersatz für das Logo.
- Dashboard / Startscreen:
  - Einstiegskarte auf dem Dashboard nutzt jetzt das Panda-Helfersystem mit i18n-Texten (`dashboard.panda.*`).

## Panda-Helfersystem

- Dateistruktur im Frontend vorbereitet:
  - `frontend/public/assets/mascot/panda_base.svg`
  - `frontend/public/assets/mascot/panda_backup.svg`
  - `frontend/public/assets/mascot/panda_bluetooth.svg`
  - `frontend/public/assets/mascot/panda_gpio.svg`
  - `frontend/public/assets/mascot/panda_security.svg`
  - `frontend/public/assets/mascot/panda_diagnostics.svg`
- Alle Varianten basieren auf der bestehenden Panda-Grafik:
  - Grundfigur: `panda_base.svg` referenziert `../branding/logo/panda-only.svg`.
  - Modul-spezifische Varianten ergänzen nur abstrakte Symbole (Backup, Sicherheit, Diagnose usw.).

## UI-Integration & Erfahrungslevel

- Neues UI-Komponenten-Modul:
  - `frontend/src/components/PandaHelper.tsx`
  - Eigenschaften:
    - `experienceLevel`: steuert Sichtbarkeit (Beginner/Fortgeschrittene/Entwickler).
    - `variant`: wählt Asset (`base`, `backup`, `bluetooth`, `gpio`, `security`, `diagnostics`).
    - `iconOnly`: Darstellung nur als Icon (ohne erklärenden Text).
  - Sichtbarkeitsregeln:
    - Einsteiger (`beginner`): Panda sichtbar, optional mit leichter Animation.
    - Fortgeschritten (`advanced`): Panda sichtbar, aber reduziert (keine forcierte Textdarstellung im Helper selbst).
    - Experten (`developer`): Panda wird im UI ausgeblendet.
- Erste Integration:
  - Dashboard-Einstiegskarte nutzt `PandaHelper` (Variante `base`) + Texte aus i18n.
  - Sidebar nutzt das Hauptlogo als primäres Branding; Panda bleibt für kontextspezifische Einsätze vorgesehen.

## i18n-Erweiterungen

- Neue Übersetzungsschlüssel in `frontend/src/locales/de.json` und `en.json`:
  - `dashboard.panda.introTitle`
  - `dashboard.panda.introBody`
  - `panda.role.helper`
  - `panda.variant.backup.tip`
  - `panda.variant.security.tip`
  - `panda.variant.diagnostics.tip`

## 2026-03-31 – Backup / Restore härten – Phase 1 (Backend-Grundlagen)

- Abschnitt: Backup / Restore
- Ziel:
  - Gefährliche Standard-Restore-Pfade nach `/` verhindern.
  - Verifikation verschlüsselter Backups differenzieren (Basis vs. Tiefenprüfung).
  - Grundlage für sichere Preview-Restores legen.
- Geänderte Dateien:
  - `backend/app.py` – Endpunkte `/api/backup/verify` und `/api/backup/restore` überarbeitet.
- Umgesetzte Punkte:
  - `/api/backup/restore`:
    - Standardmodus ist jetzt ein sicherer Preview-Restore nach `/mnt/setuphelfer-restore-preview/<timestamp>/`.
    - Root-Restore ist in dieser Phase explizit gesperrt; API liefert klaren Hinweis und Analyseinformationen.
    - Vor jedem Restore werden Archiv-Einträge analysiert:
      - Zählung von Dateien/Verzeichnissen.
      - Erkennung problematischer Einträge (Pfad-Traversal, absolute Pfade, Symlinks, Hardlinks, Sonderdateien).
      - Bei problematischen Einträgen: Abbruch mit Fehler und detaillierter Analyse, kein Entpacken.
  - `/api/backup/verify`:
    - Unterscheidung zwischen `mode: basic` und `mode: deep`.
    - Basisprüfung:
      - Existenz und Größe der Datei.
      - Für verschlüsselte Backups expliziter Hinweis, dass nur die äußere Hülle geprüft wurde.
    - Tiefenprüfung:
      - Nutzung des `BackupModule.decrypt_backup`, Entschlüsselung in ein temporäres Verzeichnis unter `/tmp/pi-installer-backup-verify`.
      - Integritätsprüfung der entschlüsselten Datei über `tar -tzf`.
      - Konsequentes Aufräumen (gelöschte entschlüsselte Datei, Entfernen des Temp-Verzeichnisses) auch bei Fehlern.
- Probleme / Risiken:
  - Produktiver Root-Restore ist bewusst weiter deaktiviert, bis Whitelist-Logik und Pfadfilterung in einer späteren Phase vollständig getestet und UI-seitig abgesichert sind.
  - Inkrementelle Restore-Ketten wurden noch nicht angepasst; aktuelle Phase konzentriert sich auf sichere Basis für Full-Backups und Preview-Restores.
- Offene Punkte:
  - UI-Anpassungen im Frontend (zweistufiger Restore-Dialog, Kennzeichnung von Basis- vs. Tiefenprüfung, Sperre für unsichere inkrementelle Restores).
  - Erweiterte Testmatrix mit realen Archiven auf Zielsystemen.
- Nächste sinnvolle Schritte:
  - Frontend-Integration der neuen Modi (`mode: 'preview' | 'root'`, `verification_mode`, `mode: 'basic' | 'deep'`).
  - Ergänzung von FAQ- und Diagnoseeinträgen für typische Fehlerbilder (Traversalsperre, verschlüsselte Verifikation, gesperrter Root-Restore).

## 2026-03-31 – Backup / Restore härten – Phase 1b (Frontend + i18n)

- Abschnitt: Backup / Restore
- Ziel:
  - Neue Backend-Härtungen (Preview-Restore, Basis-/Tiefenprüfung) in der UI sichtbar und verständlich machen.
  - Restore-Aktionen im Frontend so ausrichten, dass keine Root-Restore-Funktion suggeriert wird.
- Geänderte Dateien:
  - `frontend/src/pages/BackupRestore.tsx`
  - `frontend/src/locales/de.json`
  - `frontend/src/locales/en.json`
- Umgesetzte Punkte:
  - Restore:
    - Bisheriger „Wiederherstellen“-Flow ruft nun einen Test-Restore auf (`/api/backup/restore` mit `mode: 'preview'`).
    - Vor dem Test-Restore erfolgt eine i18n-basierte Bestätigungsabfrage („System wird nicht überschrieben“).
    - Restore-Toolbar zeigt jetzt „Analyse / Test-Restore“ als Standardaktion; Root-Restore wird UI-seitig nicht angeboten.
    - Inkrementelle Backups: Restore-Aktion wird für Dateien mit `pi-backup-inc-` blockiert; UI meldet klar, dass Restore für inkrementelle Backups aktuell nicht unterstützt wird.
  - Verifikation:
    - `verifyBackup` unterscheidet nun im Frontend zwischen Basisprüfung (`mode: 'basic'`) und Tiefenprüfung (`mode: 'deep'`).
    - Für `deep` wird ein Verschlüsselungsschlüssel über ein i18n-basiertes Prompt abgefragt und an das Backend übergeben.
    - Toaster-Meldungen wurden an das neue API-Schema angepasst (`verification_mode`, verschlüsselt/nicht verschlüsselt) und in i18n ausgelagert.
  - i18n:
    - Neue Schlüssel unter `backup.*` eingeführt (DE/EN), u. a. für:
      - Auswahlhinweise (`backup.selection.*`),
      - Basis-/Tiefenprüfung (`backup.verify.*`),
      - Test-Restore-Flows (`backup.restore.preview.*`),
      - Hinweise zur Einschränkung inkrementeller Restores (`backup.restore.incrementalNotSupported`).
- Probleme / Risiken:
  - UI zeigt aktuell nur den Preview-Status (Test-Restore); eine spätere Phase muss ggf. einen expliziten Experten-Root-Restore mit klaren Warnungen ergänzen, sobald das Backend diesen wieder erlaubt.
  - Für verschlüsselte Backups ist die Tiefenprüfung im UI an ein einfaches Schlüssel-Prompt gebunden; ein komfortablerer Schlüssel-Dialog könnte in einer späteren UX-Phase sinnvoll sein.
- Offene Punkte:
  - Darstellung detaillierter Analyseergebnisse (z. B. geblockte Pfade, systemnahe Einträge) im Restore-Tab ist vorbereitet (Struktur aus Backend vorhanden), aber noch nicht in einer eigenen UI-Sektion visualisiert.
  - Cloud-Backup-Verify nutzt weiterhin den separaten `/api/backup/cloud/verify`-Pfad; Abgleich mit den neuen Verify-Modi könnte später erfolgen.
- Nächste sinnvolle Schritte:
  - Ergänzung einer kompakten Analyse-Box im Restore-Tab, die `preview_dir`, Datei-/Verzeichnisanzahl und problematische Pfade ausgibt.
  - Umsetzung einer klaren Expertenansicht für Root-Restore, sobald Backend-Whitelist + Tests fertig sind.

## 2026-03-31 – Backup / Restore härten – Phase 1c (Analyse-UI + Deep-Verify-Dialog)

- Abschnitt: Backup / Restore
- Ziel:
  - Analyse-Ergebnisse des Preview-Restores im Restore-Tab sichtbar machen.
  - Deep-Verify-Flow von einem einfachen Browser-Prompt auf einen geführten Dialog umstellen.
- Geänderte Dateien:
  - `frontend/src/pages/BackupRestore.tsx`
  - `frontend/src/locales/de.json`
  - `frontend/src/locales/en.json`
  - `docs/faq-source-notes.md`
  - `docs/diagnostics-notes.md`
- Umgesetzte Punkte:
  - Analyse-Box:
    - Nutzt den bestehenden State `restorePreviewResult`, der nach einem erfolgreichen Preview-Restore (`/api/backup/restore` mit `mode: 'preview'`) befüllt wird.
    - Darstellung im Restore-Tab, oberhalb der Backup-Liste:
      - Backup-Datei, Preview-Verzeichnis (`preview_dir`), Gesamtzahl der Einträge (`total_entries`).
      - Aufschlüsselung nach Dateien, Verzeichnissen und sonstigen Einträgen (`total_files`, `total_dirs`, `total_other`).
      - Deutlicher Hinweis, dass das laufende System nicht überschrieben wurde (nicht-destruktiver Test-Restore).
    - Auswertung der im Backend ermittelten Listen:
      - `system_like_entries`: separate Box mit Hinweis, dass diese Pfade systemrelevant sein können (z. B. `/etc`, `/home`).
      - `blocked_entries`: deutlich hervorgehobene Warnbox; macht klar, dass problematische Archiv-Einträge erkannt und gesperrt wurden.
  - Deep-Verify-Dialog:
    - `window.prompt` im `verifyBackup`-Pfad (`mode: 'deep'`) entfernt.
    - Neuer State in `BackupRestore.tsx`:
      - `deepVerifyOpen: boolean`
      - `deepVerifyFile: string | null`
      - `deepVerifyKey: string`
    - Neuer Handler `runDeepVerify`:
      - Baut den Request-Körper mit `mode: 'deep'` und `encryption_key` auf und ruft `/api/backup/verify` auf.
      - Verwendet dieselbe Auswertung der `results`-Struktur wie die Basisprüfung (Toasts für gültig/ungültig, Beispiel-Dateien, Fehlertexte).
      - Schließt den Dialog nach Erfolg/Fehler und setzt alle Deep-Verify-States zurück.
    - Neues Modal im Restore-Screen:
      - Titel, erklärender Text, Passwortfeld, „Abbrechen“- und „Tiefe Prüfung starten“-Button.
      - Vollständig über i18n-Keys in DE/EN beschriftet.
  - i18n:
    - Ergänzung von Schlüsseln für:
      - Deep-Verify-Dialog (`backup.verify.deep.title`, `.body`, `.label`, `.placeholder`, `.cancel`, `.confirm`).
      - Analyse-Box (`backup.preview.*` – Titel, Beschreibung, Datei/Verzeichnis/Anzahl-Felder, Hinweis auf nicht-destruktiven Charakter, Texte für systemnahe und geblockte Pfade).
- Probleme / Risiken:
  - Root-Restore bleibt weiterhin gesperrt; die Analyse-Box arbeitet ausschließlich mit Daten aus dem Preview-Modus.
  - Cloud-Verify nutzt weiterhin den separaten Pfad `/api/backup/cloud/verify` und ist von der Deep-Verify-UI getrennt.
- Offene Punkte:
  - Separate Experten-UI für einen späteren Root-Restore (sofern Backend-Whitelist + Tests vorliegen).
  - Erweiterte Testabdeckung mit realen Archiven (verschlüsselt, beschädigt, gemischte Inhalte) auf Zielsystemen.

## 2026-03-31 – Backup / Restore härten – Phase 1d (Realtests & Inkonsistenzen)

- Abschnitt: Backup / Restore
- Ziel:
  - Abschnitt 1 so vorbereiten, dass ein späterer Reality-Check belastbar ist.
  - Inkonsistenzen im Bereich Verify/Restore sichtbar machen und, wo möglich, bereinigen.
- Durchgeführte technische Checks:
  - Backend-Erreichbarkeit:
    - `curl http://127.0.0.1:8000/health` → `{"status":"ok"}`.
    - Ergebnis: Backup-Backend läuft lokal und reagiert.
  - Beispiel-Fehlerfall für Verify:
    - `curl -X POST /api/backup/verify` mit `backup_file="/nonexistent/file.tar.gz"` und `mode="basic"`.
    - Antwort: `{"status":"error","message":"Backup-Datei liegt außerhalb erlaubter Pfade"}`.
    - Interpretation: Pfadvalidierung im Backend greift, aber ohne vorhandene Test-Backups war kein positiver Erfolgsfall testbar.
- Tests, die in dieser Phase nicht real ausgeführt wurden:
  - Erfolgreicher Preview-Restore auf ein echtes Archiv (inkl. Analyse-Werte und `system_like_entries`/`blocked_entries`).
  - Erfolgreiche Basis-Verifikation (`mode="basic"`) eines realen Backups.
  - Erfolgreiche Tiefe-Verifikation (`mode="deep"`) eines verschlüsselten Backups mit gültigem Schlüssel.
  - Fehlerfall „beschädigtes Archiv“ und gezielte Erzeugung problematischer Archiv-Einträge.
  - UI-Flows im Browser (Restore-Tab, Analyse-Box, Deep-Verify-Dialog) mit echten Daten.
  - Grund: In der aktuellen Umgebung wurden keine Test-Backups und keine beschädigten Archive bereitgestellt; ein automatisierter UI-Testlauf (Playwright o. Ä.) ist ebenfalls nicht konfiguriert.
- Bereinigte Inkonsistenzen:
  - Cloud-Verify:
    - Zuvor nutzte die Cloud-Toolbar fälschlich `verifyBackup(backupFile, 'gzip')` als Modus-Parameter.
    - In `BackupRestore.tsx` wurde dies auf den bestehenden Cloud-spezifischen Pfad `verifyCloudBackup` umgestellt:
      - Für jedes ausgewählte Cloud-Backup wird jetzt `/api/backup/cloud/verify` verwendet.
    - Ergebnis: Kein invalider Modus-String mehr für `verifyBackup`, klare Trennung zwischen lokalem Verify und Cloud-Verify.
- TypeScript-Einordnung für `BackupRestore.tsx`:
  - Aktuell gemeldete Fehler (Auszug aus `npx tsc --noEmit`):
    - `TS6133 'verifying' is declared but its value is never read.` – State wird geschrieben, aber im UI noch nicht ausgewertet (Altlast vor Phase 1).
    - `TS6133 'deleteBackup' is declared but its value is never read.` – Funktion existiert, ist aber nicht an die Oberfläche gebunden (Altlast vor Phase 1).
    - `TS2345` in `deleteSelectedBackups` – Typkonflikt im Callback von `requireSudo` (ebenfalls bestehend vor Abschnitt 1).
    - `TS6133 'backupFile' is declared but its value is never read.` – lokale Hilfsvariable im Cloud-Bereich (bereits im bestehenden Code vorhanden).
  - Neue Bausteine aus Phase 1b/1c/1d (Preview-Analyse, Deep-Verify-Dialog, Cloud-Verify-Bereinigung) erzeugen keine zusätzlichen TypeScript-Fehler.
- Bekannte Grenzen / Restrisiken:
  - Ohne reale Test-Backups (inkl. verschlüsselter und beschädigter Archive) bleibt das Verhalten der Analyse-Box und des Deep-Verify-Dialogs im produktnahen Szenario ungetestet.
  - Die globale TypeScript-Fehlerlage im Frontend ist weiterhin vorhanden und sollte vor einer Gesamtfreigabe separat adressiert werden.

## Bluetooth: GET /api/control-center/bluetooth/status (`get_bluetooth_status`)

- **Erkannte Fehlerfälle (Backend):**
  - `bluetooth.service_unavailable`: `bluetoothctl` fehlt (FileNotFoundError).
  - `bluetooth.adapter_missing`: Ausgabe von `bluetoothctl show` enthält „No default controller“.
  - `bluetooth.rfkill_blocked`: Erfolg (`status: success`), `enabled: false`, `code: bluetooth.rfkill_blocked` – rfkill meldet Soft/Hard block.
  - `bluetooth.unknown_error`: Timeouts, nicht-null Returncodes von `show`/`devices Connected`, OSError beim Start, unerwartete Zeilen in `devices Connected`, rfkill-Timeout/OSError.
- **Erfolg:** `status: success`, `enabled`, `connected_devices`, `code: bluetooth.ok` (bzw. `bluetooth.rfkill_blocked` bei Block).
- **Weiterhin unklar / Grenzen:** Ohne `rfkill`-Binary wird der Block-Check übersprungen; „Bluetooth aus“ nur per `rfkill` wird dann nicht von „Adapter fehlt“ unterschieden, bis `bluetoothctl show` läuft. Zustand „Powered: no“ ohne rfkill-Block liefert weiterhin `enabled: true`, solange die Geräteliste gelesen werden kann. Sehr alte `bluetoothctl`-Versionen ohne `--timeout` oder ohne `devices Connected` können `unknown_error` auslösen.

## Rescue-Stick / Read-only-Diagnose (Phase 0–1, 2026-04)

### Umgesetzt

- **Phase 0:** `docs/architecture/RESCUE_BOOT_ARCHITECTURE.md` mit Boot-States `BOOT_OK`, `BOOT_DEGRADED`, `BOOT_FAILSAFE`, Mermaid-Bootablauf, Offline/DHCP-Konzept (ohne ISO-Build).
- **Phase 1 – Backend:** `backend/modules/inspect_storage.py`, `inspect_boot.py`, `rescue_readonly_analyze.py`; Modelle `RescueFinding`, `RescueAnalyzeResponse`, `RescueRiskLevel`, optionales `DiagnosisRecord.risk_level` in `backend/models/diagnosis.py`.
- **API:** `GET /api/rescue/analyze` (`backend/api/routes/rescue.py`, Einbindung in `backend/app.py`).
- **CLI:** `scripts/rescue_mode.py` (Text- oder JSON-Stdout, Berichte unter `/tmp/setuphelfer-rescue-report.*`).
- **i18n:** `rescue.*.title` / `user_summary` in `frontend/src/locales/de.json` und `en.json`.
- **Doku:** `docs/rescue/RESCUE_DIAGNOSIS.md`, `docs/faq/RESCUE_FAQ.md`.
- **Tests:** `backend/tests/test_rescue_analyze.py` (API-Shape, UUID-Konflikt-Hilfslogik mit Patch).

### Nicht umgesetzt

- Bootstick-Image/ISO-Erstellung, Pi- und x86-Bootloader-Feinparametrisierung, WLAN-Quick-Setup, automatisches RO-Test-Mount fremder Systeme, Restore (explizit ausgeschlossen).

### Tests (durchgeführt vs. theoretisch)

- Lokal ausführbar: `python3 -m py_compile` auf neue Module; `python3 -m unittest tests.test_rescue_analyze` (setzt lauffähiges FastAPI-Backend voraus).
- **Real:** API- und CLI-Lauf auf dem Entwicklungs-Host führt echte `lsblk`/`blkid`/`findmnt`-Aufrufe aus (nur lesend); Ergebnis hängt von Hardware/Root-Rechten ab.
- **Theoretisch / simuliert:** UUID-Konflikt-Logik über `unittest.mock.patch` auf blkid-Daten.
- Nicht durchgeführt: gezielte VM-Simulation „defekte Partition“ mit erwarteten Ampel-Stufen (kein automatisierter QEMU-Lauf in dieser Änderung).

### Bekannte Grenzen

- Viele Dateisystemtypen werden nur mit blkid gelistet, ohne fsck-Pfad.
- Gateway-Erreichbarkeit per `ping` kann in gesperrten Netzen fehlschlagen, ohne dass das System „kaputt“ ist.
- Initramfs-Kennung heuristisch; false-positive „initrd_missing“ möglich.

## Rescue Restore Dry-Run (Phase 2, 2026-04)

### Umgesetzt

- Module: `rescue_backup_discovery.py`, `rescue_target_assessment.py`, `rescue_restore_dryrun.py`, `rescue_boot_restore_check.py`; zentrale Pfadregeln `core/rescue_allowlist.py`.
- Wiederverwendung: `backup_verify.verify_basic` / `verify_deep`, `restore_engine.restore_files` (nur `dry_run=True` + Pfad-Allowlist), `backup_engine`/`MANIFEST_KIND`, `backup_symlink_safety`-Logik indirekt über Restore/Verify, `inspect_boot`/`inspect_storage`-Bausteine.
- API: `POST /api/rescue/restore-dryrun` mit `RestoreDryRunRequest`/`RestoreDryRunResponse` in `models/diagnosis.py`.
- CLI: `scripts/rescue_mode.py --restore-dryrun-backup … [--target-device …] [--mode analyze_only|dryrun]`.
- Berichte: `/tmp/setuphelfer-rescue-dryrun.json` / `.md`.
- Tests: `backend/tests/test_rescue_restore_dryrun.py` (fünf Szenarien; erfordert pydantic + `/tmp/setuphelfer-test`).
- Doku: `docs/rescue/RESCUE_DRYRUN.md`, `docs/rescue/RESTORE_RISK_MODEL.md`, FAQ aktualisiert; i18n-Grundstock `rescue.dryrun.*`, `rescue.bootability.*`, `rescue.decision.*`.

### Nicht umgesetzt

- Echter Restore, Bootloader-Schreiben, Entschlüsselung echter `.gpg`-Inhalte, Image-Build.

### Tests

- `python3 -m py_compile` auf neue/geänderte Dateien (ohne venv).
- Unit-Tests der Pipeline nur mit installiertem Backend-Stack (pydantic); sonst Skip.

### Sicherheit

- Backup-Lesen und Sandbox-Schreiben strikt über Pfad-Tupel; keine Abkürzung um `restore_engine`-Allowlist; Extrakt nur unter `/tmp/setuphelfer-rescue-dryrun-staging` bzw. bestehende Verify-/Preview-Konventionen.

## Rescue kontrollierter Restore (Phase 3, 2026-04)

### Umgesetzt

- **Gating:** `backend/modules/rescue_restore_gate.py` (`validate_restore_preconditions`, Bestätigungs-Phrase, TTL-Grant); Fehlercodes `rescue.restore.RESTORE_BLOCKED_*`.
- **Ausführung:** `backend/modules/rescue_restore_execute.py` (`run_rescue_restore`, Post-Check `post_restore_validate`, Mount-Abgleich, `verify_basic`, optional Entschlüsselung, `restore_files` ohne Dry-Run nur auf Allowlist-Ziele).
- **Boot:** `backend/modules/rescue_boot_repair.py` (validieren, optional chroot/GRUB/initramfs — nur mit Flag und Ziel-Blockgerät).
- **Dry-Run-Anbindung:** Token/Grant in `rescue_restore_dryrun.py` bei erfolgreichem Dry-Run; Modelle `RescueRestoreRequest` / `RescueRestoreResponse` in `models/diagnosis.py`.
- **API:** `POST /api/rescue/restore` in `backend/api/routes/rescue.py`.
- **CLI:** `scripts/rescue_mode.py --restore-live …`.
- **Tests:** `backend/tests/test_rescue_restore_phase3.py` (gemockt, kein Schreiben auf Produktivsysteme).
- **Doku:** `docs/rescue/RESTORE_EXECUTION.md`, `docs/rescue/BOOT_REPAIR.md`, FAQ `docs/faq/RESCUE_FAQ.md`; i18n `rescue.restore.*`, `rescue.boot_repair.*`, `rescue.validation.*`.

### Bekannte Grenzen

- Boot-Reparatur-Ergebnis fließt in die HTTP-Antwort noch nicht als strukturierte Warnliste ein; Heuristik `bootable` kann von echter Hardware abweichen.
- Rollback bei fehlgeschlagenem Restore: nur manuell (Zielverzeichnis ggf. teilweise befüllt).
- Integrations-Tests ohne Mock erfordern isolierte VM/Testplatte (siehe `tools/vm-test/`).

### Sicherheit

- Token-Verbrauch nach erfolgreichem `restore_files` (Nachschärfung 3.N); kein Restore ohne übereinstimmendes Backup-/Zielgerät aus dem Grant.

## Rescue Restore Nachschärfung (Phase 3.N, 2026-04)

### Umgesetzt

- **Session-Bindung:** `session_id` in `RestoreDryRunResponse` / `RescueRestoreRequest`; Grant enthält `session_id`, optional `session_source` (`remote_db` bei Bearer-Dry-Run). Gate-Codes `rescue.restore.session_*`, `dryrun_missing`, `confirmation_missing`, `risk_ack_missing`.
- **Zielidentität:** `core/device_identity.py` (`build_device_identity`, `compare_device_identity`); Snapshot im Grant; Abgleich vor Restore.
- **Hard-Stops:** `core/rescue_hardstop.py` (Backup-Snapshot, Schlüsselpflicht, SMART kritisch, Quelle=Ziel, Identität); API prüft bei `remote_db` die authentifizierte Session gegen den Grant.
- **Gestufte Ausführung:** Stages in `rescue_restore_execute.run_rescue_restore` mit Audit in JSON+Markdown.
- **Token-Verbrauch:** erst nach erfolgreichem `restore_files`.
- **Ergebnis:** `RESTORE_BLOCKED` für harte Vorab-Blocker; Boot-Reparatur modular in `rescue_boot_repair.py` (`detect_boot_context`, …).
- **Doku:** `docs/architecture/RESCUE_STATE_MODEL.md`, `RESCUE_HARDSTOPS.md`, `RESCUE_DECISION_ENGINE.md`, `docs/rescue/BOOT_COMPATIBILITY_LIMITATIONS.md`; FAQ + `RESTORE_EXECUTION.md` erweitert.
- **Tests:** `backend/tests/test_rescue_restore_phase3.py` um Hard-Stop und Session-Gate ergänzt (mit mocks; Host ohne pydantic: Skip).

### Tests (real)

- In dieser Umgebung: `python3 -m unittest` nur wenn pydantic installiert; sonst Skip — **kein** Anspruch auf grüne CI ohne Abhängigkeiten.

### Bekannte Grenzen

- `target_mounted_active` für beliebige Pfade auf dem Root-Dateisystem ist absichtlich nicht pauschal aktiv (False Positives auf `/tmp`-Testzielen); Schutz primär über Allowlist + `target_device` + `is_running_system_disk`.
- Boot-Kontext-Erkennung bleibt heuristisch (`unknown` → keine Auto-Reparatur).

