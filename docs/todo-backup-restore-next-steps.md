# Backup/Restore – ToDo: nächste Schritte (Planung)

Diese Datei ist **reine Planungs- und Strukturierungsdokumentation**. Sie beschreibt keine Implementierung und ersetzt keine bestehenden Regeln unter `./cursor/`.

Verwandte Nachweise: [`backup-restore-realtest.md`](backup-restore-realtest.md).

---

## 1. Einleitung

### Aktueller Stand (kurz)

Für **unverschlüsselte** `.tar.gz`-Archive sind über die **HTTP-API** nachgewiesen: Verify (inkl. defekter Archive und Sicherheitsblockaden), Restore **Dry-Run** und **Preview** (Sandbox unter `/tmp`), sowie **`GET /api/system/status`** mit `realtest_state` und Ampeln. Der Nachweis wurde in einer **Docker-Testumgebung** (curl gegen laufendes Backend) erbracht; Sicherheitsmechanismen (Allowlist, Member-Analyse, Blockierung problematischer Einträge) sind implementiert und in diesen Tests greifbar.

### Was bereits erreicht ist

- API-Vertragsfelder für zentrale Erfolgs- und Fehlerpfade (inkl. `data.results` bei mehreren Verify-/Restore-Fehlern).
- Konsistente Ableitung der Ampeln aus persistiertem `realtest_state`, ohne reine Dateisystem-Heuristik für „Backup grün“.
- Dokumentierte Realtests und Testdaten-Erzeugung (`setuphelfer/create_backup_realtest_data.py`).
- Preview ohne unnötiges sudo; TTL-basiertes Aufräumen alter Preview-Verzeichnisse als Baseline.

### Was noch fehlt

- Nachweis und Abdeckung für **verschlüsselte** Backups und **Verify deep** inkl. realer Schlüssel-/Entschlüsselungsumgebung.
- **Reproduzierbare API-Tests** auf einer typischen **Host-Umgebung** ohne Docker (venv + Abhängigkeiten).
- **Abgleich** Container vs. **Zielsystem** (Pfade, Rechte, `/tmp`-Verhalten).
- Feinheiten wie **vollständige Dateilisten** in der API (derzeit Stichprobe `sample_files`), **Skalierung** sehr großer Archive, **Cleanup-Strategie** über die reine TTL hinaus – als technische und Betriebs-Themen, nicht als Grund für Rücknahme des aktuellen API-Nachweises.

---

## 2. Kategorien

| Kategorie | Inhalt |
|-----------|--------|
| **A) Kritische Erweiterungen (für vollständige Freigabe)** | Was für eine Freigabe **ohne Einschränkung „nur unverschlüsselt / nur Docker“** noch fehlt. |
| **B) Wichtige Verbesserungen** | Erhöht Vertrauen, Transparenz oder Betriebssicherheit; nicht zwingend für den bestehenden Nachweis. |
| **C) Technische Schulden** | Inkonsistenzen, begrenzte Aussagekraft einzelner Felder, dokumentierte API-Doppelungen. |
| **D) Umgebungs-/Deployment-Themen** | CI, Host, Produktion, Docker vs. Bare-Metal. |

---

## 3. ToDo-Einträge (Pflichtformat)

### A) Kritische Erweiterungen (für vollständige Freigabe)

---

#### A1 – Verify und Restore für verschlüsselte Backups end-to-end nachweisen

| Feld | Inhalt |
|------|--------|
| **Beschreibung** | API-Pfade für `.tar.gz.gpg` / `.tar.gz.enc` (und ggf. weitere konfigurierte Endungen) mit **realem** Schlüssel bzw. Test-Key durchspielen: Verify **basic** (Größe) und **deep** (Entschlüsselung + Archivprüfung), ohne Produktionsgeheimnisse in Logs. |
| **Aktueller Zustand** | Deep/verschlüsselt in [`backup-restore-realtest.md`](backup-restore-realtest.md) als **nicht API-getestet** geführt. |
| **Zielzustand** | Dokumentierter, wiederholbarer Realtest (gleiche Qualität wie unverschlüsselt); klare Erwartung für `api_status`, Fehler bei falschem/fehlendem Schlüssel. |
| **Risiko** | Ohne diesen Nachweis bleibt die Freigabe auf **unverschlüsselte** Pfade und dokumentierte Annahmen beschränkt – kein Laufzeitabsturz-Risiko, sondern **fachliche Unvollständigkeit**. |
| **Priorität** | **HOCH** |
| **Abhängigkeiten** | GPG/OpenSSL-Verfügbarkeit im Ziel-Image oder Host; sichere Handhabung von Testschlüsseln (nicht im Repo). |
| **Aufwand** | **groß** (Testdaten + Umgebung + Doku). |
| **Testanforderung** | Docker- oder Staging-Lauf mit bekanntem Test-Archiv und Key; Protokoll in `backup-restore-realtest.md` oder Folgedokument ergänzen. |

---

#### A2 – Verify `mode: deep` inkl. Entschlüsselungsfehler und Randfälle

| Feld | Inhalt |
|------|--------|
| **Beschreibung** | Gezielt testen: falsches Passwort, abgebrochene Entschlüsselung, leere Ausgabedatei, beschädigtes Archiv nach Entschlüsselung; prüfen, ob API-Contract und Logging den Regeln entsprechen. |
| **Aktueller Zustand** | Implementierung vorhanden; **kein** dokumentierter Realtest-Lauf in der Docker-Nachweisphase. |
| **Zielzustand** | Tabelle oder Checkliste mit Eingabe, erwartetem `api_status` und realem Ergebnis. |
| **Risiko** | Fehlinterpretation des Systemstatus, wenn nur „basic“ für verschlüsselt genutzt wird (`last_verify_shallow_ok` vs. voller Verify). |
| **Priorität** | **HOCH** |
| **Abhängigkeiten** | A1 (gemeinsame Test-Key-Infrastruktur). |
| **Aufwand** | **mittel** bis **groß**. |
| **Testanforderung** | Wie A1; mindestens ein negativer und ein positiver Deep-Lauf. |

---

### B) Wichtige Verbesserungen

---

#### B1 – Reproduzierbare API-Tests ohne Docker (Host mit venv)

| Feld | Inhalt |
|------|--------|
| **Beschreibung** | Einmal dokumentieren und ausführen: `venv` + `pip install -r backend/requirements.txt` (mit Freigabe), dann `TestClient` oder curl gegen `uvicorn` – gleiche Szenarien wie in Docker. |
| **Aktueller Zustand** | Host-System-Python ohne FastAPI; Nachweis primär über Docker. |
| **Zielzustand** | Kurze Anleitung im Repo + bestätigter Lauf (Datum, Umgebung); optional CI-Job nur Planung, nicht Teil dieser Datei als Implementierung. |
| **Risiko** | Entwickler/Reviewer ohne Docker können den Nachweis nicht verifizieren – **Prozessrisiko**, kein Sicherheitsloch. |
| **Priorität** | **MITTEL** |
| **Abhängigkeiten** | Freigabe für Paketinstallation; Python-Version kompatibel zu `requirements.txt`. |
| **Aufwand** | **klein** bis **mittel**. |
| **Testanforderung** | Gleiche curl-/Client-Liste wie in `backup-restore-realtest.md`; Ergebnis in Doku vermerken. |

---

#### B2 – Abgleich Produktionspfade und Berechtigungen vs. Container

| Feld | Inhalt |
|------|--------|
| **Beschreibung** | Allowlist-Pfade (`BACKUP_ALLOWED_ROOTS`), Preview-Basis, Schreibbarkeit von `config.json` für `realtest_state` auf einem **realen** Zielsystem (z. B. Raspberry Pi / Installer-Ziel) prüfen. |
| **Aktueller Zustand** | Nachweis in Container mit Bind-Mounts; [`backup-restore-realtest.md`](backup-restore-realtest.md) weist auf mögliche Abweichungen hin. |
| **Zielzustand** | Kurzes Prüfprotokoll: welche Pfade existieren, welche UID schreibt wohin, ob Preview und Persistenz funktionieren. |
| **Risiko** | Preview oder Status-Persistenz fällt auf dem Zielgerät still aus oder schlägt fehl – **mittleres Betriebsrisiko**, nicht durch Docker-Tests ausgeschlossen. |
| **Priorität** | **MITTEL** |
| **Abhängigkeiten** | Zugang zu Referenzhardware oder Staging-Image ohne Produktivdaten. |
| **Aufwand** | **mittel**. |
| **Testanforderung** | Manuell oder Skript: ein Verify, ein Preview, ein `GET /api/system/status` auf Zielhardware; Ergebnis dokumentieren. |

---

#### B3 – Sehr große Archive: Stichprobe und Performance transparent machen

| Feld | Inhalt |
|------|--------|
| **Beschreibung** | `sample_files` bleibt Stichprobe (`head -100`); `file_count` für unverschlüsselte `.tar.gz` kommt aus Member-Analyse. Für **sehr große** Archive klären: akzeptable Latenz, Timeouts, ob die API optional Hinweise liefert (z. B. „Stichprobe“), **ohne** neue Feature-Pflicht – nur Entscheidung und Doku. |
| **Aktueller Zustand** | Verhalten in [`backup-restore-realtest.md`](backup-restore-realtest.md) beschrieben; kein Messlauf mit großem Archiv. |
| **Zielzustand** | Entweder explizite **Akzeptanz** („für typische Pi-Backups ausreichend“) oder geplante kleine API-/Doku-Ergänzung in einer späteren Implementierungsphase. |
| **Risiko** | Nutzer erwartet vollständige Liste in `sample_files` – **Erwartungsrisiko**, kein Sicherheitsdefekt. |
| **Priorität** | **MITTEL** |
| **Abhängigkeiten** | Erzeugung eines großen Testarchivs (I/O-Zeit). |
| **Aufwand** | **klein** (nur Messung + Doku) bis **mittel** (falls API-Texte angepasst werden). |
| **Testanforderung** | Ein Archiv mit >100 Einträgen, eine Verify-Anfrage, dokumentierte Dauer und Response. |

---

### C) Technische Schulden

---

#### C1 – API-Antwort: Duplikate zwischen `data` und Top-Level

| Feld | Inhalt |
|------|--------|
| **Beschreibung** | Erfolgsantworten tragen `results` / `preview_dir` teils doppelt; langfristig Vereinheitlichung oder klare „kanonische“ Felder definieren – **nur planen**, nicht mischen mit UI-Themen. |
| **Aktueller Zustand** | Bewusst für Frontend-Kompatibilität beibehalten ([`backup-restore-realtest.md`](backup-restore-realtest.md)). |
| **Zielzustand** | Entscheidungsvorlage: eine Quelle der Wahrheit in der API-Spezifikation (`170_API_CONTRACT_RULES` beachten). |
| **Risiko** | Wartungsaufwand bei Änderungen; geringes Risiko inkonsistenter Clients. |
| **Priorität** | **NIEDRIG** |
| **Abhängigkeiten** | Frontend-Contract-Review in separater Phase (hier nicht ausführen). |
| **Aufwand** | **mittel** (wenn umgesetzt). |
| **Testanforderung** | Contract-Tests oder Snapshot-Liste der Felder vor/nach Änderung. |

---

#### C2 – `realtest_state`: Semantik „letzter Aufruf“ vs. „bester bekannter guter Zustand“

| Feld | Inhalt |
|------|--------|
| **Beschreibung** | Dokumentiert: `last_verify_ok` folgt dem **letzten** Verify (z. B. nach Security-Tests erneut gültiges Archiv verifizieren). Optional später: zweites Feld oder Strategie für „Production path last success“ – **nur Planung**. |
| **Aktueller Zustand** | Verhalten in Realtest-Doku erklärt. |
| **Zielzustand** | Produktentscheid, ob die Ampel so bleiben soll oder erweitert wird. |
| **Risiko** | Missverständnis bei Betrieb („Ampel rot obwohl Produktions-Backup gut“). |
| **Priorität** | **NIEDRIG** |
| **Abhängigkeiten** | System-State-Engine-Regeln (`160`). |
| **Aufwand** | **klein** (Doku) bis **groß** (falls State-Modell erweitert wird). |
| **Testanforderung** | Szenario „Verify gut → Verify evil → Status“ dokumentiert abnehmen. |

---

### D) Umgebungs-/Deployment-Themen

---

#### D1 – Docker-Image vs. produktives Deployment (DEB/systemd)

| Feld | Inhalt |
|------|--------|
| **Beschreibung** | Sicherstellen, dass das **gleiche** Backend-Paket/ dieselbe Laufzeit wie im Nachweis-Image getestet wird oder Abweichungen explizit gelistet sind (Python-Version, installierte Hilfsprogramme `tar`/`gzip`). |
| **Aktueller Zustand** | Nachweis über Repo-`Dockerfile`. |
| **Zielzustand** | Kurze Matrix: Docker | DEB-Install | Entwicklungs-venv. |
| **Risiko** | Verhalten weicht minimal ab (seltene Edge Cases). |
| **Priorität** | **MITTEL** |
| **Abhängigkeiten** | Release-Pipeline / DEB-Build. |
| **Aufwand** | **klein**. |
| **Testanforderung** | Ein identischer Verify/Preview-Lauf auf DEB-Installation, falls verfügbar. |

---

#### D2 – Preview-Cleanup über TTL hinaus

| Feld | Inhalt |
|------|--------|
| **Beschreibung** | TTL 24 h ist Baseline; optional: Betriebspolicy (max. Anzahl Verzeichnisse, Cron-Job auf dem Zielsystem, Monitoring der `/tmp`-Nutzung) – **Betrieb**, nicht zwingend Code. |
| **Aktueller Zustand** | `_cleanup_old_preview_dirs` mit `PREVIEW_SANDBOX_TTL_SECONDS`. |
| **Zielzustand** | Handbuchzeile für Administratoren oder Akzeptanz „TTL reicht für Zielgerät X“. |
| **Risiko** | Volllauf `/tmp` bei sehr vielen Previews auf kleinen Systemen – **gering** bei typischer Nutzung. |
| **Priorität** | **NIEDRIG** |
| **Abhängigkeiten** | B2 (Zielhardware). |
| **Aufwand** | **klein** (Doku) oder **mittel** (externe Automation). |
| **Testanforderung** | Kein Muss; bei Bedarf Lasttest mit vielen Previews an einem Tag. |

---

#### D3 – Parallele API-Aufrufe / gleichzeitige Previews

| Feld | Inhalt |
|------|--------|
| **Beschreibung** | Klären, ob parallel mehrere Previews nötig sind; ob Zeitstempel-Verzeichnisse ausreichen; ob Race Conditions oder Ressourcenkonflikte akzeptabel sind. |
| **Aktueller Zustand** | Nicht getestet ([`backup-restore-realtest.md`](backup-restore-realtest.md)). |
| **Zielzustand** | Entweder „nicht unterstützt / ausreichend für Einzelnutzer“ oder geplanter Lasttest. |
| **Risiko** | Seltene Verwirrung bei gleichzeitigen UI-Sessions – **gering** für typisches Einzelgerät-Szenario. |
| **Priorität** | **NIEDRIG** |
| **Abhängigkeiten** | Keine. |
| **Aufwand** | **klein** (Doku-Entscheid) bis **mittel** (Lasttest). |
| **Testanforderung** | Zwei parallele `preview`-Requests, Auswertung der `preview_dir`-Pfade. |

---

## 4. Priorisierung (Reihenfolge)

### Was als Nächstes passieren sollte (MUSS für vollständige Freigabe)

**Reihenfolge** (bewusst nicht nur sequenziell A1 → A2 → B2):

1. **A1** starten – Verschlüsselte Backups API-seitig nachweisen (inkl. Test-Key-Prozess).  
2. **Parallel dazu: B2 vorbereiten** – Zielsystem prüfen: relevante Pfade (z. B. `BACKUP_ALLOWED_ROOTS`, Preview-Basis), Rechte, benötigte Tools (GPG/OpenSSL, `tar`/`gzip`), Schreibbarkeit für `realtest_state` und Preview – damit der Abschlusslauf nicht erst nach abgeschlossenen Docker-Tests feststellt, dass das Ziel abweicht.  
3. **A2** durchführen – Verify **deep** und Fehlerpfade verschlüsselter Archive dokumentiert testen (auf dem A1-Test-Setup aufbauend).  
4. **B2 Abschlusslauf** – Referenzlauf auf **Zielhardware** oder produktionsnahem System (Verify, Preview, `GET /api/system/status`, Persistenz) unter den in Schritt 2 geklärten Bedingungen.

**Warum B2 teilweise parallel:** Verschlüsselte API-Nachweise sollen nicht **nur** im Docker-Kontext gültig sein und erst beim späteren Zielsystemlauf an Pfade, Rechten oder fehlenden Tools scheitern. Frühzeitige B2-Vorbereitung parallel zu A1 schließt diese Lücke und rückt reale Umgebung und A1/A2-Tests zeitlich näher zusammen – ohne eine neue Planungsebene; es bleibt dieselbe B2-Aufgabe, nur **Vorbereitung** vor dem **Abschlusslauf**.

### Was warten kann

- **B1** – Host-venv-Nachweis (wichtig für Entwickler ohne Docker, aber nicht identisch mit „vollständige Freigabe“).  
- **B3** – Große Archive messen und Erwartung festhalten.  
- **D1** – Matrix Docker vs. DEB.

### Optional

- **C1**, **C2** – API- und State-Refinement.  
- **D2**, **D3** – Cleanup-Policy und Parallelität.

---

## 5. Freigabebewertung (Definition)

| Stufe | Bedeutung |
|-------|-----------|
| **Eingeschränkt freigabefähig (aktueller Stand)** | Unverschlüsselte `.tar.gz`-Pfade sind **API-seitig** in der dokumentierten Docker-Umgebung nachgewiesen; Sicherheitsblockaden für problematische Archive greifen; Root-Restore bleibt gesperrt. Verschlüsselung, Deep-Verify ohne Schlüsseltest, reiner Host ohne venv und produktionsnaher Pfadabgleich sind **nicht** in gleicher Tiefe nachgewiesen. |
| **Vollständig freigabefähig (Ziel)** | Zusätzlich: **A1** und **A2** erfüllt und dokumentiert; **B2** mindestens einmal auf Ziel- oder Referenzsystem durchgeführt; keine offenen **HOCH**-Punkte aus A); bekannte Restrisiken (Stichprobe, TTL, Docker-Abweichung) sind **benannt und akzeptiert** oder durch B3/D1/D2 adressiert. |

---

*Ende der Planungsdatei – keine Implementierung in dieser Phase.*
