# Verbindliche Arbeitsregeln (Cursor / Entwicklung)

**Geltungsbereich:** Arbeit am Repository *Setuphelfer* / *PI-Installer* (Frontend, Backend, Skripte, Doku).  
**Zweck:** Vor jeder Modulbearbeitung klare Pflichten und Nachweise – keine losen Absichtserklärungen.

**Ergänzende Dateien (gleicher Ordner):**

- [MODULE_EDIT_CHECKLIST.md](./MODULE_EDIT_CHECKLIST.md) – kompakte Checkliste pro Moduländerung  
- [CHANGE_REPORT_TEMPLATE.md](./CHANGE_REPORT_TEMPLATE.md) – Pflichtgliederung für Berichte  
- [VERSIONING.md](./VERSIONING.md) – Version, Changelog, `sync-version.js`  

**Verwandte Projektdateien:** [CONTRIBUTING.md](../../CONTRIBUTING.md), [CHANGELOG.md](../../CHANGELOG.md), [docs/architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md), Website-i18n-Checkliste [docs/website/UEBERSETZUNG_CHECKLISTE.md](../website/UEBERSETZUNG_CHECKLISTE.md).

---

## Mandatory Runtime Version Gate (Pflicht vor Runtime-, Backend-, Backup-, Restore-, Rescue-, Deploy-, HW-Tests)

Vor **jedem** produktiven Testlauf, **jedem** Prompt oder Operator-Schritt, der das **laufende** Backend (Port **8000**), **`/opt/setuphelfer`**, Backup, Restore, Rescue, Deploy, **Zielpfad**-Prüfungen oder **Verify** gegen die echte Runtime voraussetzt:

1. **`./scripts/check-runtime-deploy-gate.sh`** ausführen (Exit **0**), **sofern** das Skript im Repo existiert.  
   Falls nicht vorhanden oder nur Teilkontext: mindestens **`./scripts/check-backend-version-gate.sh`** (Exit **0**) **und** manuell **`GET /api/dev-dashboard/status`** prüfen (`dashboard.deploy_drift`, optionales Deployment-Manifest).
2. **`GET /api/version`** — **HTTP 200**, gültige Payload (`status":"success"` wo definiert), **`project_version`** (bzw. `version`) **identisch** zu **`config/version.json`** im Workspace.
3. **`backend_runtime_path`** plausibel: bei **`install_profile=opt`** oder **`app_edition=release`** muss der Pfad **`/opt/setuphelfer/backend`** sein (keine Abweichung ohne dokumentierte Freigabe).
4. **`systemctl is-active setuphelfer-backend.service`** = aktiv (im kombinierten Gate-Skript enthalten).
5. **`deploy_drift`**: kein Status **gelb** mit `suggested_actions`, die **`deploy_backend_files`** oder **`restart_backend_manual`** enthalten; **`manifest_match`** darf nicht **`false`** sein, wenn Manifeste vorliegen (Details Skript/Doku).
6. **`deploy_drift`** Status **gray**: nur mit **dokumentiertem** Grund oder Umgebungsvariable **`RUNTIME_GATE_ALLOW_DEPLOY_DRIFT_GRAY=1`** (siehe `scripts/check-runtime-deploy-gate.sh` / `runtime_deploy_gate_eval.py`).

**Wenn eine Bedingung fehlschlägt:**

- **STOP.** Keine Tests gegen Port **8000**, **kein** Backup, **kein** Restore, **keine** Zielpfadprüfung am Gerät, **kein** produktives Verify, **kein** Workaround über veralteten Code unter `/opt`.
- Im Abschlussbericht **`blocked_runtime_outdated`** nennen und das Gate-Ergebnis (Exit-Code, Logzeilen) dokumentieren.
- Runbook: **`docs/operations/BACKEND_VERSION_UPDATE_GATE_DE.md`** / **`BACKEND_UPDATE_RUNBOOK_DE.md`** sowie **`docs/packaging/PACKAGE_DEPLOYMENT_GATE_DE.md`** (Paketpflicht bei abnahmefähigen Runtime-Commits).

**Hinweis:** **`scripts/check-backend-version-gate.sh`** prüft zusätzlich Produktivdateien unter `/opt` und strenge Payload-Regeln. **`scripts/check-runtime-deploy-gate.sh`** wertet danach **`deploy_drift`** über **`/api/dev-dashboard/status`** aus. **Empfohlen:** beide Skripte nacheinander ausführen, wenn das volle Gate gewünscht ist. CI ohne laufenden Dienst: nur **`RUNTIME_GATE_SKIP_DEPLOY_DRIFT=1`** setzen, wenn das **schriftlich** im Auftrag begründet ist.

---

## Mandatory Dashboard, Diagnostics and Next-Prompt Closure Rule

Jeder künftige Cursor-Lauf muss im Abschlussbericht eindeutig und nachweisbar beantworten:

1. **Dashboard-Fortschritt:** Welcher Developer-Dashboard-Bereich wurde sichtbarer, besser erklärbar oder ist von `red` auf `yellow` / `partial_green` / `green` gegangen?
2. **Diagnostik-Lernfortschritt:** Welche neue Diagnose, welcher neue Fehlercode, welcher neue Matcher oder welcher neue Testfall wurde aus dem Lauf gelernt?
3. **Next-Prompt-Entscheidung:** Was ist der nächste Prompt laut Registry, warum genau dieser, und was blockiert Alternativen?
4. **Evidence-Verknüpfung:** Welche Evidence-Dateien tragen die Aussage? Kein Bereich darf ohne belastbare Evidence künstlich auf `green` gesetzt werden.
5. **Kein Fake-Green:** `green` ist nur erlaubt, wenn Tests, Runtime-Smokes oder Hardware-/E2E-Nachweise den Status fachlich tragen. Sonst sind ehrlichere Zustände wie `partial_green`, `yellow`, `blocked`, `deferred` oder `review_required` zu verwenden.
6. **Fehler werden zur Diagnostik:** Jeder wiederholbare Fehler ist als Diagnosekandidat zu behandeln, inklusive Fehlertext, Fehlercode, Ursache, Matcher, Empfehlung, Dashboard-Bereich, Evidence-Link und Testfall.
7. **Roadmap aktualisieren:** Neue Erkenntnisse muessen gegen Roadmap, Next-Prompt-Registry und Blocker-Liste gespiegelt werden.
8. **Nicht ausgeführte Aktionen offen nennen:** Der Abschlussbericht muss ausdrücklich dokumentieren, was nicht ausgeführt wurde und was weiterhin `blocked` oder `deferred` bleibt.

Diese Closure-Regel gilt zusätzlich zu allen Runtime-/Safety-Gates. Sie erlaubt keine neuen Runtime-Aktionen und ersetzt keine echten Tests.

---

## Abschnitt 1 – Vorprüfung vor jeder Änderung

Vor Bearbeitung eines **Moduls** (oder eines klar abgegrenzten Bereichs) ist Folgendes **zu prüfen und im Bericht zu dokumentieren** (siehe [CHANGE_REPORT_TEMPLATE.md](./CHANGE_REPORT_TEMPLATE.md)):

| Thema | Inhalt |
|--------|--------|
| **Arbeitsumgebung** | z. B. Pfad des Repos, OS, Branch (wenn relevant). |
| **Vorhandene Werkzeuge** | z. B. `node`, `python3`, ob `npm`/`pytest` **ohne** neue Installation nutzbar sind. |
| **Real mögliche Prüfungen** | z. B. `npm run build` (Frontend), `ruff check`, `python -m pytest` – **nur wenn** die Umgebung das bereits hergibt. |
| **Nicht mögliche Prüfungen** | z. B. „`pytest` nicht installiert, bewusst kein `pip install`“ – **explizit benennen**. |
| **Betroffene Module/Dateien** | Konkrete Pfade, keine Pauschalbehauptungen. |
| **Modulstatus vor Änderung** | Kurz: **i18n** (vollständig / teilweise / hart kodiert), **Diagnose** (ja/nein/teilweise), **Doku** (aktuell/veraltet/unbekannt), **FAQ** (in-app / `docs/` – betroffen ja/nein), **Wissensbasis** (welche Datei/Kapitel), **Changelog** (letzter relevanter Eintrag), **Version** (`config/version.json`). |

---

## Abschnitt 2 – Keine Installationen ohne Notwendigkeit

- **Nicht** automatisch installieren: `pip install`, `apt install`, `npm install`, `cargo add` – nur um eine Prüfung „irgendwie“ zu ermöglichen.
- Wenn ein Werkzeug fehlt: **Grenze dokumentieren** („in dieser Umgebung nicht ausführbar“) und stattdessen **statische Prüfung** oder **CI-Verweis** (.github/workflows/ci.yml) nennen.
- **Ausnahme:** nur wenn das Projektteam / die Aufgabenstellung ausdrücklich eine Installation verlangt (dann im Bericht begründen).

---

## Abschnitt 3 – Nicht getestet ist nicht erfolgreich

Im Bericht und in Commit-/PR-Texten klar trennen:

| Kategorie | Bedeutung |
|-----------|-----------|
| **Real getestet** | Befehl wurde ausgeführt, Ergebnis genannt (z. B. Exit-Code, Build ok). |
| **Statisch geprüft** | z. B. Datei gelesen, Diff reviewed – **kein** Laufzeittest. |
| **Nicht geprüft** | bewusst weggelassen – **kein** Erfolgsnachweis. |
| **In dieser Umgebung nicht möglich** | Tool fehlt oder Zugriff fehlt – siehe Abschnitt 2. |

**Verboten:** Formulierungen wie „fertig“, „vollständig“, „läuft“ ohne Zuordnung zu einer der Kategorien.

---

## Abschnitt 4 – Modulvollständigkeit

Wird ein Modul geändert, sind die folgenden **Aspekte zu prüfen**. Wird einer **nicht** angepasst, **Begründung im Bericht** (Scope, Risiko, Follow-up).

| Aspekt | Pflicht |
|--------|---------|
| **Frontend-Code** | Geänderte Komponenten/Seiten, Konsistenz mit bestehenden Mustern. |
| **Backend-Code** | API, Module, Fehlerantworten – falls das Modul Backend hat. |
| **i18n** | Siehe Abschnitt „i18n-Pflicht“ unten. |
| **Diagnose** | Nutzung von `POST /api/diagnosis/interpret`, lokale Diagnose, Spezialendpunkte – falls vorhanden; sonst „nicht betroffen“ begründen. |
| **Typen/Schemas** | TS-Typen ↔ Pydantic/OpenAPI wo relevant. |
| **Dokumentation** | Technisch (`docs/…`), Nutzer (in-app Handbuch, `docs/user/…`). |
| **FAQ / Wissensbasis** | In-app-Dokumentation, `docs/faq-source-notes.md`, ggf. Troubleshooting-Kapitel. |
| **Changelog** | [CHANGELOG.md](../../CHANGELOG.md) und laut [VERSIONING.md](./VERSIONING.md) ggf. In-App-Changelog (`Documentation.tsx`). |
| **Versionsnummer** | Bei relevanter Änderung `config/version.json` anheben, `frontend/node sync-version.js` ausführen (wenn Node vorhanden). |

---

## i18n-Pflicht (jedes bearbeitete Modul)

1. **Neue sichtbare UI-Texte** dürfen **nicht** dauerhaft hart kodiert werden (Ausnahme: technische IDs, Log-Marker, reine Daten aus der API ohne Präsentationsstring).
2. **Neue** Nutzer sichtbare Strings: über **i18n-Keys** in `frontend/src/locales/de.json` und `frontend/src/locales/en.json`, Einbindung per `useTranslation()` / `i18n.t` wie im bestehenden Code.
3. **Scope:** Bei einer Moduländerung sind die **direkt betroffenen** harten Texte **mitzu prüfen** und **soweit im Auftrag enthalten** zu migrieren.
4. **Toasts, Modals, Status-, Hilfe- und Fehlermeldungen** gehören zur UI – **i18n-pflichtig**, sofern neue oder geänderte Texte.
5. **de/en-Key-Parität:** Jeder neue Key in **beiden** Dateien; Abweichungen nur mit dokumentierter Ausnahme.
6. **Große Textblöcke** (z. B. ganze Handbuchkapitel): **schrittweise** Migration zulässig, aber mit **Restliste** im Bericht.
7. **Backend-Texte**, die **unverändert** im UI erscheinen (Fehlermeldungen, Diagnose-Records): auf **Sprachlogik** prüfen; wenn nur Deutsch: im Bericht als **technische Schuld / offen** kennzeichnen.

**Technische Guardrails (ESLint o. ä.):**  
Aktuell **keine** zusätzliche erzwungene Lint-Regel „keine Literal-Strings“ eingeführt (Risiko: False Positives, Wartungsaufwand). **Verbindlich** gilt die **Prozessregel** oben. Eine spätere automatische Regel nur nach Abstimmung und Testlauf.

---

## Pflegepflicht: Doku, FAQ, Wissensbasis, Changelog, Version

### Entscheidungsmatrix (bei jeder **relevanten** Änderung prüfen)

| Frage | Bei „Ja“ |
|--------|-----------|
| Muss die **technische** Doku angepasst werden? | `docs/architecture/`, `docs/developer/`, modulbezogene `.md` aktualisieren. |
| Muss die **Nutzer**-Doku angepasst werden? | In-app `Documentation.tsx`, `docs/user/`, `docs/user/QUICKSTART.md` o. ä. |
| Muss die **FAQ** ergänzt werden? | In-app FAQ-Abschnitte, `docs/faq-source-notes.md` bei Quellnotizen. |
| Muss die **Wissensbasis** ergänzt werden? | Entsprechende Kapitel/Dateien (Handbuch, Troubleshooting, `docs/review/` nur wenn dort der Kanal definiert ist). |
| Muss das **Changelog** ergänzt werden? | [CHANGELOG.md](../../CHANGELOG.md) + gemäß VERSIONING In-App-Liste. |
| Muss die **Versionsnummer** erhöht werden? | [VERSIONING.md](./VERSIONING.md) – i. d. R. ja bei sichtbaren oder dokumentationsrelevanten Änderungen. |

### Richtlinie Versionen (Kurzfassung; Details in VERSIONING.md)

| Stufe | Wann |
|--------|------|
| **Patch (W)** | Kleine Bugfixes, kleine i18n-/Doku-/Diagnosekorrekturen, Prozess-/Doku-Ergänzungen ohne neues Feature. |
| **Minor (Z)** | Neue Funktionen, neue Diagnosepfade mit Nutzerwirkung, größere Modulverbesserungen (Schema: Z↑, W→0). |
| **Major (X/Y)** | Inkompatible oder strukturelle Brüche (selten; gesondert abstimmen). |

**Nicht angepasst** → im Bericht **explizit begründen** (z. B. „reine interne Refactor, kein Changelog laut Team“ – nur wenn so vereinbart).

---

## Standard-Bericht (Pflichtgliederung)

Für jede **relevante** Aufgabe das Format in [CHANGE_REPORT_TEMPLATE.md](./CHANGE_REPORT_TEMPLATE.md) verwenden (Abschnitte: Umgebung, Ist-Zustand, Umsetzung, i18n, Diagnose, Doku/FAQ/KB, Version/Changelog, Prüfung, Offene Punkte).

---

## CI-Hinweis (Nachweis, kein lokaler Installationsauftrag)

Im Repository ist in [.github/workflows/ci.yml](../../.github/workflows/ci.yml) definiert, dass auf GitHub u. a. `pip install -r requirements.txt`, `ruff`, `bandit` und `pytest` laufen. **Lokal** gilt weiterhin: keine Installation nur „für den Agenten“, wenn die Umgebung das nicht schon bietet – stattdessen CI als Referenz nennen.

---

## Stand dieser Regeln

Diese Datei beschreibt **Prozess- und Qualitätsregeln**. Sie ersetzt keine Code-Review-Entscheidung und **erzwingt** Verhalten nicht technisch (außer durch Teamdisziplin und PR-Review). Ergänzungen: per PR mit Changelog-Eintrag gemäß VERSIONING.md.

---

## Pflichtregel: Keine Background-/Auto-Ketten durch Cursor

Cursor darf **keine** Background-Tasks, Auto-Efficiency-Ketten, Ingest-Jobs, Commit-/Push-Ketten oder spaetere Statusmeldungen ankuendigen oder starten.  
Jeder Lauf endet **synchron** mit vollstaendigem Schlussbericht.  
Wenn eine Aktion Operatorrechte benoetigt, wird ein **Operator-Handoff** erstellt, aber **keine** Hintergrundausfuehrung gestartet.
