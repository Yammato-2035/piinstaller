# FAQ – Backup & Restore – Deutsch

## Muss vor Backup-/Restore-Tests das Backend-Version-Gate grün sein?

**Ja.** Solange **`GET /api/version`** nicht **HTTP 200** mit **`status":"success"`** liefert oder die produktive **`config/version.json`** nicht dem freigegebenen Schema entspricht, sind Testergebnisse nicht belastbar. Zuerst **`scripts/check-backend-version-gate.sh`** und das Update-Runbook (`docs/operations/BACKEND_UPDATE_RUNBOOK_DE.md`) — **kein** Backup-Start bei `blocked_update_required`.

## Die Weboberfläche ist unter Port 3001 nicht erreichbar. Was prüfen?

1. **Backend:** `curl -s http://127.0.0.1:8000/api/version` — muss `success` liefern; sonst `setuphelfer-backend.service` prüfen.
2. **Web-UI-Dienst:** `systemctl is-active setuphelfer.service` — muss **active** sein.
3. **Port:** `ss -ltnp | grep ':3001'` und `curl -I http://127.0.0.1:3001` — erwartet **HTTP 200**.
4. **Runtime-Gate:** `./scripts/check-runtime-deploy-gate.sh` — Exit **0** vor Backup/BR-001.
5. **Dienst inactive/dead mit Exit 0/SUCCESS:** Historisch: Vite Preview im **Vordergrund** (`exec npm run preview …`), nicht im Hintergrund (`&` + `wait`). Aktuell: **`serve-frontend-production.py`** (stdlib) statt Vite-Preview. Details: **`docs/operations/WEB_UI_RUNTIME_SERVICE_DE.md`**, KB **`docs/knowledge-base/runtime/WEB_UI_SERVICE_INACTIVE_EXIT0.md`**, Evidence `docs/evidence/runtime-results/setuphelfer_web_ui_runtime_repair_2026-05-18.json`, `docs/evidence/runtime-results/web_ui_reload_crash_repair_2026-05-19.json`.

**Kein Backup**, Restore oder Verify Deep starten, bis Backend, Web-UI und Gate grün sind.

## Warum bedeutet tar Exitcode 1 nicht automatisch ein kaputtes Backup?

GNU **tar** verwendet Exitcode **1** für „mit Warnungen beendet“ (z. B. **Datei hat sich beim Lesen geändert**, **Socket ignoriert**). Das Archiv kann trotzdem vollständig sein — Setuphelfer wertet das **nicht** allein aus dem Exitcode ab. Details und BR-001-Forensik: **`docs/backup/TAR_EXIT_1_CLASSIFICATION_DE.md`**, Evidence `docs/evidence/runtime-results/br001_tar_exit1_forensics_2026-05-16.json`.

## Warum akzeptiert Setuphelfer tar Exit 1 nicht blind?

Der Runner (`backup_runner.py`) bricht bei **`returncode != 0`** mit **`abort_reason: tar_failed`** ab, entfernt die `.partial` und erzeugt **kein** finales Archiv — damit kein SHA256 und kein Verify Deep. Das verhindert „Warnung = Erfolg“ ohne Nachweis. Der Runner klassifiziert stderr und schreibt u. a. `tar_warning_classification` in den Jobstatus. **Volatile-only** führt nur nach erfolgreicher Finalisierung **und** Verify Deep zu `backup.success_with_warnings` / `completed_with_warnings` — nicht zu normalem `backup.success`. Ohne finales Archiv bleibt der Lauf fehlgeschlagen (`backup.warning_not_promoted`). Deploy der Runner-Version nach `/opt` ist weiterhin ein separater Schritt.

## Warum werden volatile Live-Dateien gesondert klassifiziert?

Pfade wie **Journal**, **~/.cache**, **Agent-Sockets** (gpg, ibus, Docker Desktop) ändern sich während eines langen Full-Backups normal. Sie sind von **kritischen** Pfaden (`/etc`, `/boot`, …) zu trennen. Nur erlaubte volatile Muster dürfen überhaupt in Betracht kommen, den Job von „hart fehlgeschlagen“ herabzustufen — siehe **`docs/knowledge-base/backup/TAR_EXIT_1_LIVE_FILES.md`**.

## Warum bleiben SHA256 und Verify Deep nach Warnungen zwingend?

Exitcode und stderr beweisen **keine** Integrität des gzip/tar-Streams. Setuphelfer verlangt ein **finales** `.tar.gz`, eingebettetes **MANIFEST.json**, Payload-**SHA256** und **Verify Deep**, bevor ein Lauf mit tar-Warnungen als Erfolg gelten könnte.

## Warum gibt es ohne finales Archiv keinen Erfolg?

Ohne Rename von `.partial` zu `.tar.gz` fehlt das Artefakt für Hash, Manifest und Restore. Beispiel Job **`927469d42503`**: ~227 GiB geschrieben, danach Exit **1**, **`partial_deleted: true`** — Status bleibt **`backup.failed`**, Verify wird **nicht** gestartet.

## Wann wird nach einem Backup eine E-Mail gesendet?

Nur wenn der Job **`backup.success`** meldet oder **`backup.success_with_warnings`** mit verifizierter Integrität (Verify Deep im Runner ok). Keine Mail bei Fehlschlag oder `warning_not_promoted`. Details: **`docs/backup/BACKUP_NOTIFICATIONS_DE.md`**.

## Wie konfiguriere ich SMTP und eine Testmail?

Unter **Einstellungen → E-Mail-Benachrichtigungen**: Empfänger, SMTP-Daten, **Verschlüsselung** (`SSL/TLS` für Port 465 oder `STARTTLS` für Port 587) und Mailbox-Passwort setzen, **Speichern**, dann **Testmail senden**. Das Passwort wird in der UI nicht angezeigt.

## Warum schlägt ein SMTP-Fehler das Backup nicht fehl?

Der Mailversand ist **optional** und **nachgelagert**. Scheitert SMTP, bleibt `notification_email_status: failed`, der Backup-Status bleibt Erfolg. Zugangsdaten gehören in `.env` oder systemd, **nicht** ins Git-Repository (siehe `.env.example`).

## Warum dauert ein Full-Root-Backup so lange und skaliert schlecht mit vielen CPU-Kernen?

**gzip** (und klassisches **`tar -czf`**) komprimiert im Wesentlichen **single-threaded**. Viele Kerne helfen kaum; oft limitieren **I/O** und **eine CPU** den Durchsatz. **pigz** nutzt mehrere Threads, bleibt aber **gzip-kompatibel** (schneller, wenn installiert). **zstd** ist schneller/skaliert besser, erfordert aber eine **durchgängige** Pipeline inkl. Finalisierung/Manifest — bis dahin bleibt das Produkt **gzip-kompatibel**. Ein **vollständiges Root-Backup** ist bewusst ein **Experten-/Langläuferpfad**; für Alltag und Pi eignen sich **kleinere Profile** (siehe **`docs/backup/BACKUP_PERFORMANCE_DE.md`**, Profilübersicht **`docs/backup/BACKUP_PROFILES_DE.md`**, Testmatrix **BR-016**, **BR-019**).

## Welche Profile gibt es in der UI?

Standard ist **„Empfohlenes Backup“** (`recommended`). **Expertenmodus / vollständiges Root-Backup** (`full-expert`) ist sichtbar getrennt und erfordert eine Checkbox; Legacy-API `type: full` verhält sich wie **full-expert** inkl. Warnungen. Details und API: **`docs/backup/BACKUP_PROFILES_DE.md`**, Endpunkte `/api/backup/profiles` und `/api/backup/profile-preview`.

## Was ist mit Fortschritt, ETA und Evidence?

Der Runner füllt **`progress_optional`** (u. a. Phase, Durchsatz, **`eta_seconds`** nur bei belastbarer Schätzung sonst **`null`**). Nach Job-Ende kann ein **Evidence-Paket** erzeugt werden (Logs, `systemctl`, `journalctl`-Auszüge, Mounts) — siehe **`docs/backup/BACKUP_EVIDENCE_COLLECTOR_DE.md`** (**BR-017**). UI-Hinweise: **`backup.messages.*`** in den Locale-Dateien (z. B. langsamer Lauf, Kompression als Flaschenhals, Paketblocker, ETA).

## Warum darf das Backup nicht auf dem Root-Dateisystem liegen?

Ein Backup auf dem gleichen Dateisystem wie das laufende System ist unsicher. Bei einem Festplattenfehler, einer Fehlbedienung oder einem Restore-Fehler kann das Backup gleichzeitig mit dem Original verloren gehen.

## Warum wurde `/mnt/setuphelfer/backups` blockiert?

Der Pfad lag auf dem Root-Dateisystem und war kein eigenes sicheres Zielmedium. Die Storage-Schutzlogik hat deshalb korrekt blockiert.

## Warum war `/media/...` zunächst blockiert?

Die frühere Logik blockierte `/media` pauschal. Das war zu streng, weil Linux-Desktop-Systeme externe Datenträger typischerweise unter `/media/<user>/...` einhängen.

## Wie wurde das korrigiert?

`/media` wird nicht pauschal freigegeben. Ein Ziel unter `/media` ist nur erlaubt, wenn es auf ein echtes, sicheres Blockgerät zeigt und nicht System-, Boot-, Windows- oder EFI-Partition ist.

## Welche externen Medien bevorzugt Setuphelfer als Backup-Ziel?

Setuphelfer soll Backups **auf externen Datenträgern** ablegen — **nicht** auf Root-, Boot- oder Systemplatte. Priorität (höchste zuerst): **externe NVMe**, **externe SSD**, **externe HDD**, **USB-Stick**, **SD-Karte**. Interne NVMe mit `/` oder andere interne Systempfade sind ungeeignet. Details: `docs/backup/BACKUP_TARGET_POLICY_DE.md`, `docs/knowledge-base/backup/BACKUP_TARGET_SELECTION.md`.

## Was bedeutet der strategische Pfad `/media/setuphelfer/setuphelfer-back`?

Das ist ein **konventioneller Zielpfad in der Doku**, der **nur** genutzt werden darf, wenn er **wirklich auf dem ausgewählten externen Medium** liegt (Mount-Quelle ist ein externes `/dev/...`, nicht das Root-Dateisystem). Setuphelfer legt ihn **nicht automatisch** an, **formatiert** nicht und **verschiebt** keine bestehenden Mounts. Wenn Ihr externes Volume bereits unter z. B. `/media/<Benutzer>/setuphelfer-back` hängt, gibt es **keine** automatische Umdeutigung — das ist eine **Betreiberfreigabe** (Mount/Bind/Policy).

## Was passiert, wenn Setuphelfer das Ziel nicht traversieren oder nicht beschreiben darf?

Dann wird **kein** Ausweichen auf interne Pfade erzwungen. Nach aktuellem Backend-Stand im Workspace meldet die API u. a. **`backup.target_traverse_denied`** mit Diagnose **STORAGE-PROTECTION-006**. Der Nutzer/Betrieb muss **Freigaben oder Mount/Rechte** klären.

## Warum formatiert oder partitioniert Setuphelfer nicht automatisch?

Daten auf externen Platten sollen erhalten bleiben. Ohne eindeutiges, sicheres externes Ziel bleibt Backup **blockiert**.

## Warum muss `/media` beim Full-Backup ausgeschlossen werden?

Wenn `/` gesichert wird, würde `/media` sonst externe Datenträger mit in das Backup aufnehmen. Das kann zu riesigen Backups, rekursiven Läufen oder Stalls führen.

## Welche Pfade sind bei Full-Backup ausgeschlossen?

Mindestens:

- `/proc`
- `/sys`
- `/dev`
- `/tmp`
- `/run`
- `/mnt`
- `/media`
- `/run/media`
- konkreter Backup-Zielpfad

## Warum blieb das Backup hängen?

Der konkrete Lauf blieb bei ca. 27,46 GB stehen. Wahrscheinliche Ursachen waren:

- zu breiter Quellumfang inklusive `/media`
- mögliches Pipe-Blocking durch tar stdout/stderr

## Was wurde geändert?

- `/media` und `/run/media` wurden als Excludes ergänzt.
- stdout wird nicht mehr gepuffert.
- stderr wird während des Laufs konsumiert.

## Was ist nach dem Fix noch zu tun?

Ein neuer Full-Backup-Lauf muss erfolgreich abgeschlossen werden. Danach müssen Manifest, Basic Verify und möglichst Deep Verify geprüft werden.

## Wann ist Monolith-Refactoring erlaubt?

Erst wenn:

- Target-Check erfolgreich ist
- Full Backup erfolgreich ist
- Manifest vorhanden ist
- Verify erfolgreich ist

## Warum bricht Deep-Verify mit „Integrität“ oder Symlink-Meldungen ab?

Deep-Verify prüft Archive streng (u. a. Symlinks und Staging-Containment). **Full-Root-Archive** können absolute oder aus Sicht des Staging-Roots „ausbrechende“ Symlink-Ziele enthalten — dann liefert die API z. B. `backup.verify_integrity_failed`, ohne dass das Speichermedium zwingend defekt ist. Abhilfe: Kontext prüfen, ggf. Basic-Verify nutzen und die technische Notiz in der Wissensdatenbank lesen (`docs/knowledge-base/BACKUP_VERIFY_PREVIEW_RUNTIME.md`, Diagnose-ID `VERIFY-STAGING-038`).

## Warum schlägt Restore-Preview mit „No space left on device“ fehl, obwohl die Backup-Platte groß ist?

Preview extrahiert unter **`/tmp`** bzw. unter dem für den **Backend-Dienst** gültigen **`TMPDIR`**, oft in einem **PrivateTmp**-Namespace. Ein kleines **tmpfs** oder volles Dienst-`/tmp` führt zu **ENOSPC**, selbst wenn `/mnt/...` viel frei hat. Abhilfe: großes persistentes Verzeichnis wählen, **`TMPDIR`** per systemd-Drop-In setzen, Dienst neu starten. Siehe `docs/knowledge-base/BACKUP_VERIFY_PREVIEW_RUNTIME.md` und Diagnose `RESTORE-TMPFS-007`.

## Warum stirbt das Backend bei Verify/Preview mit OOM oder cgroup-Kill?

Ein zu kleines **`MemoryMax`** (oder fehlender Swap/SwapMax) in der **systemd-Unit** des Backends begrenzt den realen RAM für den Prozess; große Archive übersteigen das leicht. Abhilfe: `MemoryMax` / `MemorySwapMax` in einer Drop-In-Datei unter `setuphelfer-backend.service.d/` anheben, `daemon-reload`, Dienst neu starten. Details: `docs/knowledge-base/BACKUP_VERIFY_PREVIEW_RUNTIME.md`, Diagnose `SYSTEMD-MEMORYMAX-037`.

## Was erkennt Inspect in Phase 0/1?

Inspect liest nur Rohdaten: Blockgeraete, Filesysteme, Mountstatus, UUID-Konflikte, Bootstatus und Netzwerkstatus.
Die Antwort kommt strukturiert ueber `GET /api/inspect/run`.

## Warum repariert Inspect noch nichts?

Phase 0/1 ist bewusst defensiv und read-only. Es werden keine Schreiboperationen auf Zielmedien ausgefuehrt.

## Warum wird Windows nur erkannt, aber nicht veraendert?

Inspect liefert nur Hinweis-Flags (z. B. `possible_windows`, `possible_dualboot`) und fuehrt keine Partitionierungs-, Bootloader- oder Restore-Aktionen aus.

## Warum gibt es noch keine Handlungsempfehlung?

In Phase 0/1 werden nur Daten gesammelt und stabil per Codes bereitgestellt. Bewertung, Ampel und konkrete Aktionsvorschlaege sind explizit nicht Teil dieser Phase.

## Was liefert Inspect in Phase 2 zusaetzlich?

Phase 2 ergaenzt `GET /api/inspect/run` um `classification` (Systemtyp, Vertrauenswert, Indikatoren-Codes, Risikostufe) und `advice` (empfohlene Wege als **Codes** mit Prioritaet). Es werden **keine** Reparatur-, Restore- oder Deploy-Schritte gestartet.

## Warum kann das System falsch klassifiziert werden?

Die Klassifikation nutzt nur die **bereits gesammelten** Rohdaten (z. B. erkannte FS-Typen, Boot-Codes). Fehlende Geraete, versetzte Platten, reine Datenpartitionen oder Rescue-Kontext koennen zu **UNKNOWN** oder **PARTIAL_SYSTEM** fuehren — das ist bewusst defensiv.

## Warum wird Windows nicht automatisch repariert?

Inspect fuehrt **keine** Schreiboperationen und **keine** Bootloader-/Partitions-Aktionen aus. Windows-Erkennung ist eine **Interpretation**, keine Freigabe fuer Eingriffe.

## Warum sind Empfehlungen keine Aktionen?

`advice.recommended_paths` sind **strukturierte Hinweise** fuer Menschen/Prozesse ausserhalb von Inspect (`requires_confirmation` ist immer aus Sicht „nicht automatisch ausfuehren“ gedacht). Die UI zeigt diese Codes **ohne** ausloesende Buttons.

## Warum kann ich meine Platte nicht auswählen (Write-Safety)?

Die Oberfläche zeigt nur den **Status** aus Inspect (`write_safety_summary` / `GET /api/safety/targets`). Wenn ein Datenträger **gesperrt** ist (z. B. Systemplatte, Dualboot-Muster, unsicheres NTFS), gibt es **keinen** Button zum Überspringen — das ist bewusst.

## Warum wird „Windows“ blockiert?

Allein **NTFS** oder ein Windows-ähnliches Layout ohne klares **Backup-Kandidaten-Muster** führt zu **`SAFETY_WINDOWS_DETECTED`** — automatische Freigabe für Schreibzugriffe erfolgt **nicht**.

## Warum gibt es keinen Override in Phase 1?

Write-Safety liefert nur **Codes** und Kennzeichen (`requires_override` dokumentiert mögliche spätere Prozesse). Eine UI zum Aufheben der Sperre ist **nicht** Teil dieser Phase.



## Warum wird vor Restore/Deploy nochmal gesichert?

Preflight-Backup ist die letzte defensive Sicherung, bevor spaetere Eingriffe starten. So bleibt ein Rueckfallpunkt erhalten, falls Folgeaktionen scheitern.

## Warum brauche ich eine Bestätigung?

`/api/preflight/backup/execute` akzeptiert nur ein planbezogenes `confirmation_token` aus `preview`. Ohne Token wird nicht ausgefuehrt.

## Warum darf ich nicht auf jede Platte sichern?

Write-Safety blockiert riskante Ziele (Systemdisk, Live-Medien, Windows-/Dualboot-Risiko, unbekannte Geraete). Preflight respektiert diese Sperren strikt.


## Warum gibt es erst Preview?

Der Rescue-Orchestrator prüft zuerst nur Safety, Verify und Dryrun. Das minimiert Risiko, bevor irgendeine echte Rückschreibung erlaubt wäre.

## Warum wird noch kein Restore ausgeführt?

Phase 1 enthält ausschließlich `POST /api/rescue/preview`. Es gibt in dieser Stufe keinen neuen Execute-Endpunkt.

## Warum blockiert Safety mein Ziel?

System-, Live-, Windows-, Dualboot- und unbekannte Ziele bleiben strikt blockiert.

## Warum wird Preflight empfohlen?

Wenn kein passender Preflight-Plan nachweisbar ist, markiert der Preview-Lauf dies als Warnung (`RESCUE_PREFLIGHT_RECOMMENDED`).


## Warum braucht Restore eine Preview-Session?

Execute ist nur aus einer vorherigen, gültigen Preview erlaubt. Ohne Session-ID + Token wird geblockt.

## Warum muss ich nochmal bestätigen?

Das Token ist plan-/sessiongebunden und läuft ab. Dadurch gibt es keine globale Restore-Freigabe.

## Warum prüft Setuphelfer vor Execute nochmal Safety und Verify?

Zwischen Preview und Execute kann sich der Zustand ändern (Zielgerät, Mounts, Backup-Datei). Deshalb werden Safety und Verify erneut geprüft.

## Warum wird Boot-Repair noch nicht automatisch ausgeführt?

Phase 2 trennt Dateirestore und Boot-Reparatur bewusst. Ein automatisches Boot-Repair ist in dieser Stufe nicht Teil des Execute-Flows.

## Warum prüft Setuphelfer nach Restore nochmal?
Der Dateirestore kann technisch erfolgreich sein, obwohl Zielstruktur oder Boot-Artefakte unvollständig sind. Die Post-Restore-Validation prüft deshalb rein lesend auf Plausibilität.

## Warum ist ein Restore trotz Warnung nicht automatisch fehlgeschlagen?
Warnungen markieren Nacharbeit (z. B. fehlende `fstab`, fehlende Setuphelfer-Artefakte), aber sie bedeuten nicht zwingend, dass der Restore unbrauchbar ist.

## Warum wird Boot-Repair nur empfohlen?
In dieser Phase werden keine Reparaturaktionen ausgelöst. Fehlende Kernel-/Initramfs-Artefakte führen nur zu `POST_RESTORE_BOOT_REPAIR_RECOMMENDED`.

## Warum wird Setuphelfer nicht automatisch installiert?
Post-Restore-Validation ist bewusst read-only. Fehlende Setuphelfer-Artefakte werden als Warnung gemeldet, ohne automatische Installation.

## Warum prüft Setuphelfer Bootfähigkeit?
Ein Dateirestore kann erfolgreich sein, obwohl Boot-Artefakte fehlen. Die Boot-Capability-Prüfung ergänzt daher eine reine Lesebewertung.

## Warum heißt „wahrscheinlich bootfähig“ nicht garantiert bootfähig?
Die Bewertung ist defensiv und basiert auf plausiblen Artefakten (fstab, Kernel, Initramfs, Hinweise), nicht auf einem echten Bootvorgang.

## Warum wird Windows/Dualboot nicht automatisch repariert?
Windows-/Dualboot-Fälle sind risikoreich und werden nur erkannt und als Warnung/Manual-Review markiert.

## Warum gibt es noch keinen Boot-Repair-Button?
Diese Phase ist bewusst read-only. Reparaturaktionen sind nicht Teil des aktuellen API-Umfangs.

## Warum repariert Setuphelfer Boot noch nicht automatisch?
Der Boot Repair Plan in dieser Phase liefert nur theoretische Vorschläge. Ausführung ist bewusst deaktiviert.

## Warum ist Boot Repair riskant?
Falsches Zielgerät, unbekanntes Layout oder fehlerhafte Bootloader-Schritte können Systeme unbootbar machen.

## Warum muss ich manuell entscheiden?
Bootreparaturen sind sicherheitskritisch. Setuphelfer markiert deshalb riskante Fälle mit Manual-Review.

## Warum werden Windows/Dualboot nicht automatisch repariert?
Windows-/Dualboot-Setups haben hohes Risiko für Überschreiben oder Boot-Konflikte und bleiben manuell.

## Was ist der Recovery Report?
Der Recovery Report fasst alle vorhandenen Rescue-Ergebnisse strukturiert zusammen (Inspect, Safety, Preflight, Preview, Execute, Post-Restore, Boot).

## Warum ist ein Restore trotz Warnung nicht automatisch fehlgeschlagen?
Warnungen markieren Risiken oder Nacharbeiten, aber nicht zwingend einen technischen Totalfehler.

## Warum werden manche Aktionen blockiert?
Blockierungen folgen Sicherheitsregeln (z. B. kein Restore ohne gültige Preview/Token, keine automatische Windows-/Dualboot-Reparatur).

## Warum zeigt Setuphelfer Empfehlungen statt automatisch alles zu machen?
Diese Phase ist bewusst defensiv und advisory-only. Kritische Aktionen bleiben explizit manuell bestätigt.

## Warum gibt es keinen „Fix All“-Button?
Boot-Reparaturen sind risikobehaftet. Phase 2 erlaubt nur einzelne, explizit bestätigte Aktionen.

## Warum sind manche Reparaturen blockiert?
Windows-, Dualboot- und High-Risk-Fälle werden defensiv blockiert.

## Warum brauche ich ein Token?
Das Token bindet die Ausführung an genau eine Session, ein Ziel und eine Aktion.

## Warum wird Boot nicht automatisch repariert?
Automatische Kaskaden sind in dieser Phase ausgeschlossen. Jede Reparatur muss einzeln bestätigt werden.

## Was ist ein Recovery-Minimalsystem?
Ein Recovery-Minimalsystem ist ein bewusst schlanker Zielzustand, um ein System wieder erreichbar zu machen (z. B. per SSH + Setuphelfer-Backend) — in dieser Phase nur als Plan.

## Warum wird SSH nicht automatisch aktiviert?
Automatische Remote-Öffnung ist sicherheitskritisch und bleibt manuell bestätigt.

## Warum wird Setuphelfer nicht automatisch installiert?
Phase 1 ist rein advisory. Installationsschritte werden nur als erforderliche Schritte ausgewiesen.

## Warum wird Windows/Dualboot blockiert?
Diese Layouts sind risikoreich und werden defensiv nicht automatisch behandelt.

## Warum passiert beim Execute noch nichts?
Diese Phase liefert nur Session- und Contract-Validierung. Reale Schritte folgen erst in einer späteren Ausführungsphase.

## Warum brauche ich eine Session?
Die Session bindet Token, Zielpfad und ausgewählte Schritte eindeutig zusammen.

## Warum kann ich nicht sofort SSH aktivieren?
SSH-Aktivierung ist sicherheitskritisch und in der Prep-Phase bewusst blockiert.

## Was passiert in der nächsten Phase?
In der nächsten Phase können klar begrenzte Schritte mit denselben Sicherheitsregeln kontrolliert ausgeführt werden.

## Warum ist SSH nach Phase 2b noch nicht aktiv?
Phase 2b zeichnet nur sichere Vorbereitungen auf. Eine echte SSH-Aktivierung bleibt gesondert freizugeben.

## Warum wird nur eine Recovery-Notiz geschrieben?
Die Notiz ist ein nachvollziehbarer, risikoarmer Startpunkt ohne direkte Systemaktivierung.

## Warum wird Setuphelfer nur vorbereitet?
Nur lokale Quellen werden geprüft und vorbereitet. Start/Enable von Diensten ist noch nicht erlaubt.

## Warum gibt es keine automatische Fernwartung?
Automatische Fernwartung erhöht das Risiko und ist in dieser Phase bewusst ausgeschlossen.

## Was bedeutet „Activation“?
Activation bedeutet in dieser Phase nur einen Sicherheits- und Ablaufplan zur späteren Erreichbarkeit.

## Warum wird SSH nicht automatisch aktiviert?
SSH-Aktivierung bleibt ein separater, ausdrücklich bestätigter Schritt.

## Welche Ports werden geöffnet?
In dieser Plan-Phase werden keine Ports real geöffnet. Es wird nur modelliert, welche betroffen wären.

## Warum ist das System noch nicht erreichbar?
Der Activation-Plan ist advisory-only und startet keine Dienste.

## Warum passiert beim Activation Execute noch nichts?
Activation Execute Prep prüft nur Session, Token und Plan-Bindung. Reale Aktivierung folgt erst in der nächsten Phase.

## Warum ist ein Token nötig?
Das Token verhindert unautorisierte Aktivierung und bindet die Ausführung an genau eine Session.

## Warum wird SSH noch nicht aktiviert?
SSH-Aktivierung bleibt sicherheitskritisch und ist in dieser Phase ausdrücklich ausgeschlossen.

## Was folgt in Controlled Activation?
Erst dort werden einzeln freigegebene Schritte unter strengen Sicherheitsregeln tatsächlich ausgeführt.

## Warum nur SSH-Key und kein Passwort?
Passwort-Login wird im Zielsystem bewusst als deaktiviert vorbereitet. Damit bleibt der Remote-Zugang auf schluesselbasierte Authentisierung begrenzt.

## Warum kein Root-Login?
Root-Login per SSH ist ein Hochrisiko-Pfad. Deshalb wird `PermitRootLogin no` im Ziel vorbereitet und nicht aufgehoben.

## Warum wird das Host-System nicht geändert?
Controlled Execute schreibt nur unter `target_path`. Laufendes Host-System, laufende Dienste und Host-Accounts bleiben unberuehrt.

## Warum ist Fernwartung nach diesem Schritt nicht garantiert?
Diese Phase bereitet nur Teilbausteine vor. Ob ein Ziel danach wirklich erreichbar ist, haengt weiterhin von Zielzustand, Netzwerk und manueller Freigabe ab.

## Warum braucht LAN-Bind eine ausdrückliche Bestätigung?
Ein LAN-Bind kann den Backend-Port im Netz sichtbar machen. Deshalb ist `allow_lan_backend_bind=true` explizit noetig und erzeugt eine Warnung.

## Wann darf ein Deploy durchgeführt werden?
Nur wenn Inspect und Write-Safety ein **leeres** oder **explizit leer** signalisiertes Ziel zeigen (z. B. `SAFETY_EMPTY_DISK` auf allen betrachteten Platten). Alles andere bleibt blockiert oder erfordert manuelle Pruefung.

## Warum wird meine Platte blockiert?
Typische Gruende: Systemplatte, Live-Medium, Windows-/Dualboot-Muster, bereits befuellte Datenpartitionen oder unklare Safety-Signale. Der Deploy-Plan folgt diesen Hard-Stop-Regeln.

## Warum kein automatisches Installieren?
Die Deploy-Phase liefert nur einen **Plan** mit Codes und Profilen. Installation, Partitionierung und Schreibzugriffe sind bewusst ausgeschlossen.

## Welche Profile gibt es?
Logische Vorschlaege (z. B. minimales Linux, Webserver, Backup-Knoten, NAS-artig, experimentell) ohne Image-Bezug. Kein Profil wird automatisch ausgefuehrt.

## Warum passiert beim Deploy Execute noch nichts?
Die aktuelle Deploy-Execute-Prep-Phase prueft nur Session, Token sowie Plan-/Ziel-/Profil-Bindung und liefert danach `DEPLOY_EXECUTE_READY`.

## Warum ist ein Token nötig?
Das Token bindet die Freigabe an genau eine Deploy-Session und verhindert unkontrollierte Ausfuehrung.

## Warum muss ein Profil gebunden werden?
Die Session ist an ein konkretes, als geeignet markiertes Profil gebunden, damit spaetere Phasen keine stillen Profilwechsel ausfuehren.

## Was folgt in Deploy Preview?
Die naechste Phase validiert konkrete Installationsschritte als Vorschau (Dry-Run/Preview), bevor irgendeine echte Ausfuehrung erlaubt wird.

## Warum wird noch nichts installiert?
Deploy Preview ist eine Simulation und liefert nur einen kontrollierten Vorschaulauf mit Codes.

## Warum wird remote_image nicht geladen?
In dieser Phase wird `remote_image` nur formal validiert (URL/Checksum), Download bleibt bewusst blockiert.

## Warum zeigt Preview schreibende Schritte?
Die Liste zeigt, welche Schritte in späteren Phasen potenziell schreiben würden. In Preview selbst wird nichts ausgeführt.

## Was folgt nach Deploy Preview?
Nach Preview folgt eine streng kontrollierte Execute-Phase mit zusätzlicher Freigabe und erneuten Sicherheitsprüfungen.

## Warum werden keine Images heruntergeladen?
Die Source-Registry ist rein metadata-basiert. Downloads sind in dieser Phase aus Sicherheitsgruenden deaktiviert.

## Warum sind manche Sources blockiert?
Blockierte Quellen sind bewusst fuer die aktuelle Plattform/Policy gesperrt oder verletzen Defensivregeln.

## Warum wird Architektur geprüft?
Falsche Architektur fuehrt spaeter zu unbootbaren oder nicht startbaren Systemen. Die Pruefung reduziert dieses Risiko fruehzeitig.

## Warum gibt es Experimental Sources?
Experimental Sources dienen nur der transparenten Risikoabbildung und sind klar als high-risk markiert.

## Warum lädt Setuphelfer noch kein Image?
Die Cache-Plan-Phase ist rein planerisch. Downloads werden aus Sicherheitsgruenden noch nicht gestartet.

## Warum ist eine Checksumme Pflicht?
Ohne erwartete Checksumme kann die Integritaet des Images nicht defensiv abgesichert werden.

## Warum werden interne URLs blockiert?
Interne/localhost URLs bergen Missbrauchs- und Fehlkonfigurationsrisiken und sind deshalb in dieser Phase gesperrt.

## Warum wird der Cache nur geplant?
Damit alle Schritte transparent und pruefbar bleiben, bevor spaeter eine kontrollierte Ausfuehrungsphase freigegeben wird.

## Warum nur lokale Images?
Diese Phase ist bewusst local-only, damit keine unkontrollierten Remote-Bezüge stattfinden.

## Warum wird die Checksumme geprüft?
Wenn ein erwarteter Hash vorliegt, wird die Integritaet der lokalen Datei vor der Cache-Freigabe abgesichert.

## Warum wird das Image nicht gemountet?
Mount/Entpacken ist in dieser Sicherheitsstufe nicht erlaubt; es erfolgt nur Dateivalidierung und kontrolliertes Kopieren.

## Warum darf nicht jeder Cachepfad genutzt werden?
Schreiben ist nur unter erlaubten Setuphelfer-Cacheprefixen erlaubt, um Pfadmissbrauch und Traversal zu verhindern.

## Warum wird das Image nicht gemountet?
Deploy Image Inspect ist bewusst read-only auf Dateimetadaten beschraenkt. Mount/Loop/Entpacken ist in dieser Phase sicherheitshalber ausgeschlossen.

## Warum reicht Dateiendung nicht als Sicherheitsnachweis?
Die Endung zeigt nur einen Namenshinweis, aber keine Integritaet oder Herkunft. Deshalb wird optional SHA256 geprueft und bei Unsicherheit defensiv gewarnt/geblockt.

## Warum wird Architektur nicht garantiert erkannt?
Ohne Inhaltsanalyse des Images kann die Architektur nicht belastbar bestimmt werden. Die API liefert daher `DEPLOY_IMAGE_ARCHITECTURE_UNVERIFIED`.

## Warum muss das Image im Setuphelfer-Cache liegen?
Nur erlaubte Cache-Pfade sind fuer spaetere Deploy-Flows freigegeben. Das reduziert Pfadmissbrauch und verhindert ungepruefte Fremdpfade.

## Warum wird noch nicht geschrieben?
Deploy Write Plan ist bewusst eine reine Simulation. Datentraeger-Schreiben, Partitionierung und Formatierung bleiben in dieser Phase deaktiviert.

## Warum ist Zielbestätigung mehrfach nötig?
Mehrere Bestaetigungen reduzieren Fehlbedienung bei destruktiven Folgephasen. Ziel, Datenverlust und finale Freigabe werden getrennt abgesichert.

## Warum wird Windows/Dualboot blockiert?
Windows-/Dualboot-Layouts tragen hohes Risiko fuer Datenverlust und Boot-Konflikte. Deshalb blockiert die Safety-Logik diese Faelle hart.

## Was passiert nach dem Write Plan?
Nach erfolgreichem Write Plan folgt erst eine spaetere, separat freizugebende Execute-Phase mit erneuten Sicherheitspruefungen.

## Warum wird noch nichts geschrieben?
Die aktuelle Deploy-Write-Execute-Phase ist ein Dry-Run-Contract. Es werden nur Session, Token und Re-Checks validiert und simulierte Schritte zurueckgegeben.

## Warum sind so viele Bestätigungen nötig?
Die Bestaetigungen sind absichtlich redundant, damit Zielgeraet, Datenverlust und Bildquelle nicht versehentlich freigegeben werden.

## Warum wird das Ziel mehrfach geprüft?
Zwischen Plan, Session und Execute kann sich Kontext aendern. Der Dry-Run prueft Zielbindung deshalb direkt vor der simulierten Ausfuehrung erneut.

## Was passiert in der echten Write-Phase?
Eine spaetere echte Write-Phase muss separat freigegeben werden und bleibt ausserhalb dieses Dry-Run-Contracts.

## Warum noch ein zusätzlicher Bestätigungsschritt?
Der Final-Confirmation-Schritt reduziert Fehlbedienungen unmittelbar vor einer spaeteren Real-Write-Phase und erzwingt explizite Letztfreigaben.

## Warum Snapshot/Fingerprint?
Snapshot und Fingerprint binden die Freigabe an ein konkretes Zielbild aus vorhandenen Daten und machen stille Zielwechsel erkennbar.

## Warum wird weiterhin nichts geschrieben?
Final Confirmation bleibt ein reiner Dry-Run-Gate. Es validiert nur Konsistenz und Bestätigungen ohne Datentraegerzugriff.

## Was folgt nach Final Confirmation?
Danach kann in einer spaeteren, separat freigegebenen Phase ein echter Write-Flow vorbereitet werden.

## Warum wird noch nicht auf echte Datenträger geschrieben?
Der Test Harness ist absichtlich isoliert und erlaubt nur Testdateien. Echte Blockdevice-Schreibpfade bleiben gesperrt.

## Warum nur Testdateien?
So kann die Write-Logik verifiziert werden, ohne produktive Datentraeger zu gefaehrden.

## Warum ist max_bytes begrenzt?
Die Byte-Grenze reduziert Risiko und begrenzt den Testumfang auf kontrollierbare Groessen.

## Was folgt nach dem Test Harness?
Nach stabilen Harness-Tests kann eine spaetere produktive Write-Phase separat geplant und freigegeben werden.

## Warum noch kein echtes Schreiben?
Der Real-Write-Guard ist bewusst nur eine Sicherheits- und Freigabeschicht ohne Write-Engine.

## Warum nur removable?
Nicht-removable Ziele haben ein hoeheres Risiko fuer Systemdisk-Fehltreffer und werden deshalb hart blockiert.

## Warum Harness-Pflicht?
Ohne erfolgreichen isolierten Harness-Nachweis wird Real-Write-Vorbereitung fail-closed blockiert.

## Warum Snapshot/Fingerprint?
Der Fingerprint bindet die Freigabe an einen konkreten Zielzustand und erkennt Drift zwischen Session und Check.

## Warum keine Systemplatten?
Systemdisk-, Windows-, Dualboot-, LVM-, RAID- und Loop-Faelle bleiben in dieser Phase strikt blockiert.

## Warum nur USB/SD?
Das Hardware-Gate markiert nur entfernbare Testmedien mit passendem Transport als potenziell testfaehig.

## Warum blockiert Hardware-Gate nicht mehr automatisch bei globalem DUALBOOT?
Die Bewertung ist jetzt target-scoped: Ein globaler Host-Zustand wie `DUALBOOT` oder `UNKNOWN` erzeugt Warnung/Review, blockiert aber nicht mehr automatisch ein sauberes Zielmedium.

## Warum wurde aus review_required wieder test_ready?
Nach dem Metadaten-Fix werden Zielinfos (`removable`, `transport`, `size`, `rotational`) konsistenter aus Inspect/lsblk und Parent-Disk-Mapping uebernommen. Dadurch faellt ein sauberes `/dev/sdb` nicht mehr wegen fehlender Felder auf `review_required`.

## Warum kein internes Laufwerk?
Interne/nicht-removable Laufwerke werden defensiv blockiert, um Fehlziele bei spaeteren destruktiven Phasen zu vermeiden.

## Warum Operator-Checks?
Physische Gegenkontrolle reduziert Verwechslungen, die aus rein softwarebasierten Signalen nicht sicher ausgeschlossen werden koennen.

## Warum physische Kontrolle nötig?
Geraete koennen zwischen den Schritten umgesteckt, ausgetauscht oder neu gemountet werden; deshalb bleibt eine manuelle Endkontrolle Pflicht.

## Warum noch kein echtes Schreiben?
Diese Phase liefert nur Gate- und Protokollinformationen. Eine echte Write-Engine ist weiterhin nicht vorhanden.

## Gibt es jetzt doch echtes Schreiben?
Nur den **Real-Write-Prototyp** (`POST /api/deploy/write/prototype`): streng begrenzt, nur mit Feature-Flag, nur removable USB/SD, max. 512MB, reines Python-I/O, mit Verify. Kein vollwertiger Installer und kein allgemeiner Write-Endpunkt.

## Warum nur removable Medien im Prototyp?
Fehlziele auf fest eingebauten Platten sind deutlich schwerer operativ auszuschliessen; der Prototyp bleibt auf entfernbare Testmedien beschraenkt.

## Warum 512MB Limit im Prototyp?
Begrenzt Schaden und Laufzeit bei ersten echten Schreibtests; groessere Images sind bewusst ausgeschlossen.

## Warum kein dd im Prototyp?
`dd` und Shell-Tools sind schwerer auditierbar (Fehlerquellen, Rechte, unerwartete Flags). Reines Python-I/O ist linear nachvollziehbar und ohne Subprocess.

## Warum kein Windows-/Dualboot-Ziel?
Diese Ziele bleiben in der Sicherheitskette blockiert (Inspect/Safety/Hardware-Gate), um Datenverlust auf gemischten Layouts zu vermeiden.

## Warum noch kein echter Installer nach dem Prototyp?
Der Prototyp schreibt roh ein einzelnes Image-Fragment; es gibt keine Partitionierung, kein Bootloader-Setup, kein unattended Setup; das waere eine separate, explizit freigegebene Phase.

## Warum kein Retry beim Real-Write-Prototyp?
Retries wuerden echte Fehler (falsches Ziel, Drift, Teilwrite) verdecken und das Risiko erhoehen; die Pipeline bricht bewusst hart ab.

## Warum sofortiger Abort bei Drift?
Zwischen Gate und Write kann sich der Zustand des Mediums aendern (Mount, Readonly, Pfad). Ein sofortiger Abort verhindert Writes gegen einen nicht mehr gueltigen Kontext.

## Warum ist Device-Drift kritisch?
Der Fingerprint und die Live-Signale (Mount, RO, Groesse) muessen zum freigegebenen Snapshot passen; andernfalls besteht Fehlziel- oder Datenkorruptionsrisiko.

## Warum ist Verify strikt?
Verify vergleicht exakt die geschriebene Byteanzahl ohne stille Korrektur; Mismatch oder kurze Reads fuehren zu einem klaren Fehlercode ohne Reparaturversuch.

## Was sind die Failure-Injection-Hooks?
Nur mit `SETUPHELFER_REAL_WRITE_TESTMODE=1`: kontrollierte Simulationsvariablen (`FAIL_BEFORE_OPEN`, `FAIL_AFTER_OPEN`, `FAIL_AFTER_CHUNKS`, `FAIL_VERIFY_MISMATCH` + Pfad, `FAIL_DURING_FSYNC`, `FAIL_DEVICE_CHANGED`). Siehe `docs/deploy/DEPLOY_REAL_WRITE_FAILURE_INJECTION_DE.md`.

## Warum ein separater Deploy-Write-Runner statt Backend als root?
Das Backend bleibt unprivilegiert; ein kleiner One-Shot-Runner kann spaeter gezielt erhoehte Rechte fuer Blockdevice-I/O erhalten, ohne die gesamte API-Oberflaeche zu vergroessern.

## Was ist das Deploy-Write-Jobfile?
Ein lokales JSON mit `job_hash`-Bindung (SHA256 ueber kanonische Daten ohne Hash-Feld), Zielgeraet, Image-Pfad/Checksum/Groesse, Guard-Metadaten und festen Constraints. Siehe `docs/deploy/DEPLOY_WRITE_RUNNER_CONTRACT_DE.md`.

## Was macht der Runner in dieser Phase?
Nur `--dry-run`: Job laden, validieren, JSON-Ergebnis auf stdout — kein Device oeffnen, kein Schreiben. CLI: `backend/tools/deploy_write_runner.py`.

## Warum ist sudoers fuer den Runner heikel?
Jede Regel mit `NOPASSWD` erhoeht den Schaden bei kompromittiertem Account; Wildcards in der sudoers-Zeile und ein zu grosszuegiges `env_keep` koennen Argument- oder Bibliotheks-Injection ermoeglichen (`PYTHONPATH`, `LD_PRELOAD`). Deshalb: feste Pfade, minimale Umgebung, Details in `docs/evidence/DEPLOY_WRITE_RUNNER_RUNTIME_VALIDATION.md`.

## Warum One-Shot statt root-Backend oder Daemon?
Ein kurzlebiger Prozess mit genau einem Job reduziert Angriffsflaeche und Zustand; ein dauerhaft root-laufendes Backend oder ein privilegierter Daemon wuerde Netzwerk- und Session-Risiko mit erhoehten Rechten verbinden.

## Warum Lockfiles fuer den Deploy-Runner?
Exklusive Lock-Datei pro Job verhindert parallele Doppel-Ausfuehrung auf demselben Ziel-Job; Stale-Erkennung (PID/TTL) verhindert harte Blockaden nach Absturz. Siehe `docs/deploy/DEPLOY_RUNNER_LIFECYCLE_DE.md`.

## Warum eine Lifecycle-State-Machine?
Klare erlaubte Phasen und Terminalzustaende machen das Verhalten auditierbar und verhindern stille „Spruenge“ (fail-closed). Uebergaenge sind explizit; ungueltige werden blockiert.

## Warum Audit-Log (JSON Lines)?
Nachvollziehbare Ereignisreihe ohne Geheimnisse (keine vollen Checksummen/Tokens in der Zeile); unterstuetzt Betrieb und Post-Mortem. Verzeichnis `runner-audit/`.

## Warum Stale-Lock-Cleanup?
Ohne Aufraeumen koennte ein verwaistes Lock nach Prozessende echten Betrieb blockieren; Cleanup entfernt tote oder TTL-ueberschrittene Locks kontrolliert.

## Warum TOCTOU-Rechecks?
Zwischen Validierung und (spaeterem) Write aendern sich Medien, Mounts oder Metadaten; wiederholte read-only Abgleiche vor kritischen Schritten reduzieren das Fenster fuer inkonsistente Zustaende.

## Warum ein separater Backend->Runner-Handoff?
Damit das Backend unprivilegiert bleibt und nur einen streng definierten Dry-run-Auftrag an den isolierten Runner uebergibt; keine freien Shell-Befehle und kein direkter Device-Zugriff im Backend.

## Warum Jobdateien fuer den Handoff?
Jobdateien sind auditierbar, hash-gebunden und lokal validierbar. Der Runner kann denselben Input erneut pruefen (fail-closed), bevor irgendein spaeterer privilegierter Schritt erlaubt waere.

## Warum atomisches Schreiben?
`.tmp` + Rename verhindert halbfertige Jobdateien bei Abbruch/Crash und reduziert Race-/TOCTOU-Risiken beim Lesen durch den Runner.

## Warum Dry-run-Runner im Handoff?
Der komplette Ablauf (Create -> Start -> JSON-Response) wird realistisch geprobt, ohne echte Device-Aktionen auszufuehren.

## Warum ist `subprocess.run` hier erlaubt?
Nur fuer den lokalen One-Shot-Runner mit festen Argumenten, `shell=False`, kontrolliertem `cwd`, minimaler Umgebung und Timeout. Keine freien Kommandos.

## Warum keine automatische sudoers-Installation?
Automatische sudoers-Aenderungen sind hochriskant und schwer ruecknehmbar. Deshalb liefert die Boundary-Phase nur ein read-only Policy-Modell statt Systemeingriff.

## Warum feste Runner-Pfade?
Absolute, stabile Pfade reduzieren PATH-/Symlink-Manipulation und verhindern, dass ein anderer Interpreter oder ein anderes Skript gestartet wird.

## Warum PYTHONPATH blockiert?
Ein gesetztes `PYTHONPATH` kann Imports auf manipulierte Module umlenken. Darum wird es im Boundary-Audit als kritisch markiert.

## Warum ist LD_PRELOAD gefaehrlich?
`LD_PRELOAD` kann beliebigen Code vor dem eigentlichen Programm laden und damit Sicherheitsannahmen aushebeln; deshalb wird es blockiert.

## Warum keine echte Root-Sandbox in dieser Phase?
Diese Phase ist bewusst simuliert: Policies werden modelliert und getestet, ohne echte Privilegwechsel oder Systemeingriffe. So bleiben Risiken kontrolliert.

## Warum keine echten Signale senden?
Signalpfade werden nur als Modell (`would_send_signals`) beschrieben, damit keine unbeabsichtigten Prozessabbrueche in laufenden Umgebungen entstehen.

## Warum stdin deaktivieren?
Ein nicht-interaktiver One-shot-Runner darf keine Laufzeit-Eingaben erwarten; deaktiviertes stdin reduziert Interaktions- und Injection-Risiken.

## Warum minimale ENV?
Je kleiner die vererbte Umgebung, desto geringer das Risiko durch manipulierbare Loader-/Interpreter-Variablen und PATH-Mehrdeutigkeiten.

## Warum One-shot-Runner?
Kurze Laufzeit, definierter Input/Output und kein Hintergrundmodus reduzieren Fehlerflaeche, Zombie-/Orphan-Risiken und unkontrollierte Zustandsakkumulation.

## Warum kein Root-Backend?
Ein root-laufendes Backend vergroessert die Angriffsoberflaeche massiv. Der Plan erzwingt stattdessen einen kleinen, spaeteren One-shot-Runner mit klarer Rechtegrenze.

## Warum kein dauerhafter Runner-Service?
Ein Daemon mit dauerhaften Rechten erhoeht Persistenz- und Angriffsrisiken. Das Service-Modell bleibt bewusst one-shot und ohne Netzwerklistener.

## Warum wird sudoers nur geplant?
Sudoers-Aenderungen sind hochsensibel und werden daher in dieser Phase nur als Audit-/Plantext modelliert, nicht installiert oder ausgefuehrt.

## Warum ist manuelle Installation noetig?
Pfad-, Eigentums- und Rechtepruefungen sind sicherheitskritisch und muessen im Zielsystem kontrolliert/reviewt erfolgen; automatische Anwendung ist absichtlich deaktiviert.

## Wie sollte Rollback aussehen?
Rollback soll dokumentiert sein: entfernte Snippets, rueckgenommene Verzeichnisrechte und verifizierter Dry-run ohne Privilegpfad, bevor Betrieb fortgesetzt wird.

## Warum nur Dry-run-Validator?
Die Phase prueft ausschliesslich Bereitschaft und Sicherheitsgrenzen. So bleiben Risiken kontrollierbar, bevor manuelle Privilegschritte ueberhaupt geplant umgesetzt werden.

## Warum kein visudo im Validator?
Der Validator arbeitet komplett read-only gegen uebergebenen Snippet-Text. Systemweite Pruefung/Installation bleibt ein separater manueller Schritt ausserhalb dieser Phase.

## Warum sind fehlende Pfade nur review_required?
Fehlende Zielpfade bedeuten oft nur "noch nicht manuell vorbereitet". Das ist ein Review-Thema, solange keine harten Sicherheitsverletzungen vorliegen.

## Warum ist Rollback Pflicht?
Privilegierte Integrationen brauchen einen klaren Rueckbaupfad, damit Fehlkonfigurationen schnell und reproduzierbar entfernt werden koennen.

## Warum nur Blueprint?
Der Blueprint trennt Planung von Ausfuehrung: Sicherheit, Rechte und Pfade werden zuerst transparent modelliert, ohne Systemeingriff.

## Warum kein automatisches Paket?
Automatisches Paketieren/Installieren kann Fehlkonfigurationen breit ausrollen. Deshalb bleibt die Phase auf Manifest und Review begrenzt.

## Warum wird sudoers nicht automatisch installiert?
Sudoers ist besonders kritisch; Installation bleibt ein manueller, kontrollierter Schritt mit separater Freigabe.

## Warum steht Rollback im Manifest?
Rollback muss von Beginn an definiert sein, damit Rueckbau reproduzierbar und auditierbar bleibt.

## Warum ist Validierung nach Installation Pflicht?
Nach manueller Einrichtung muss der Dry-run-Validator plus erneuter Runtime-Proof sicherstellen, dass keine Sicherheitsannahme gebrochen wurde.

## Warum Konsistenzpruefung?
Mehrere Planebenen reduzieren Risiko nur dann, wenn sie denselben Sicherheitsvertrag abbilden; die Konsistenzpruefung entdeckt Widersprueche frueh.

## Warum muessen Pfade in allen Ebenen gleich sein?
Abweichende Runner-/Job-/Sudoers-Pfade erzeugen Umgehungsrisiken und machen Freigaben unverlaesslich.

## Warum werden Rollback-Schritte abgeglichen?
Ein unvollstaendiger Rueckbaupfad kann Systeme in unsicherem Zwischenzustand lassen; daher muessen Pflichtcodes uebergreifend vorhanden sein.

## Warum sind Validation-Steps nicht automatisch?
Validation bleibt ein kontrollierter manueller Sicherheitsprozess; automatische Ausfuehrung koennte fehlerhafte Annahmen unbemerkt fortschreiben.

## Warum noch nicht production-ready?
Kritische Hardware- und Privilegvalidierungen sind noch offen; deshalb bleibt die Freigabe bewusst unterhalb einer Produktionsfreigabe.

## Was bedeutet ready_for_lab?
`ready_for_lab` bedeutet: kontrollierte Labor-/Testumgebung ist moeglich, aber produktive Real-Write-Freigabe bleibt gesperrt.

## Warum blockieren Hardware-E2E-Luecken?
Ohne belastbare Hardware-E2E-Nachweise bleibt das Risiko fuer reale Medien-/Timing-Fehler zu hoch.

## Warum ist ein sudoers-Runtime-Test erforderlich?
Policy-Text allein reicht nicht: erst der Runtime-Nachweis bestaetigt, dass Pfad-/Env-Grenzen in der Zielumgebung korrekt greifen.

## Warum bleibt Failure-Injection auf echter Hardware noetig?
Nur echte Hardware zeigt Hotplug-, Reenumeration- und Race-Effekte realistisch; reine Simulation deckt diese Klassen nicht vollstaendig ab.

## Warum ein Lab-Plan vor weiterer Umsetzung?
Der Plan priorisiert kritische Nachweise, bevor weitere Integrationsschritte folgen, und reduziert Risiko durch klare manuelle Gates.

## Warum feste Reihenfolge?
Die Reihenfolge minimiert Fehlinterpretationen: erst Policy-/Dry-run-Nachweise, dann Hardware-nahe Szenarien und zuletzt Rollback.

## Warum nur ein Testmedium?
Ein einzelnes eindeutig markiertes Medium reduziert Verwechslungs- und Fehladressierungsrisiken deutlich.

## Warum Operator-Abbruchbedingung?
Unsicherheit des Operators ist selbst ein Sicherheitsindikator; Tests muessen dann sofort gestoppt werden.

## Warum kein automatischer Testlauf?
Hardware-nahe Sicherheitsnachweise benoetigen kontrollierte manuelle Beobachtung und Entscheidungen vor Ort.

## Warum muss ein sudoers-Runtime-Test geplant werden?
Nur ein strukturiertes Testdesign stellt sicher, dass Policy-Annahmen, ENV-Grenzen und Dry-run-Verhalten reproduzierbar geprueft werden.

## Warum wird sudo nicht automatisch ausgefuehrt?
Automatische Privilegaufrufe sind in dieser Phase bewusst verboten; Ausfuehrung bleibt ein spaeterer, kontrollierter manueller Schritt.

## Warum ist visudo nur manuell vorgesehen?
Die Syntax-/Policy-Pruefung ist sicherheitskritisch und soll unter direkter Operator-Kontrolle mit lokalem Kontext erfolgen.

## Warum sind negative sudoers-Tests noetig?
Negative Faelle zeigen, dass unsichere Konfigurationen (env_keep, Wildcards, generische Aufrufe) fail-closed blockiert werden.

## Warum muss privilegierte Validierung geplant werden?
Der Schritt verknuepft Sudoers-, Laufzeit-, Lifecycle- und Audit-Nachweise zu einem konsistenten Dry-run-Pruefpfad vor jeder spaeteren Real-Write-Freigabe.

## Warum wird trotzdem kein echter Root-Runner gestartet?
In dieser Phase bleibt alles bei Testdesign und Review; echte privilegierte Ausfuehrung ist absichtlich ausgeschlossen.

## Warum ist --dry-run Pflicht?
Nur mit erzwungenem Dry-run lassen sich Privileg- und Kontrollpfade pruefen, ohne Device-Risiko einzugehen.

## Warum muessen UID/GID dokumentiert werden?
UID/GID-Nachweise belegen, in welchem Kontext der Runner effektiv lief und ob die geplante Privileggrenze korrekt umgesetzt waere.

## Warum sind negative Tests vor Real-Write noetig?
Sie beweisen fail-closed Verhalten bei Hash-, Pfad-, ENV- und Lock-Fehlern, bevor echte Medien beruehrt werden.

## Warum wird der erste echte Write nur geplant?
Der erste Hardware-E2E-Write ist hochriskant und wird deshalb zuerst als kontrollierter, auditierbarer manueller Plan ausgearbeitet.

## Warum nur Wegwerfmedium?
Nur ein entbehrliches Medium begrenzt potenziellen Schaden, falls trotz Kontrollen etwas unerwartet passiert.

## Warum ist SHA256-Verify Pflicht?
Die Verify-Pruefung belegt Ende-zu-Ende-Datenintegritaet und verhindert stilles Weiterlaufen bei fehlerhaftem Write.

## Warum kein Retry bei Verify-Mismatch?
Ein Mismatch ist ein harter Sicherheitsindikator; Wiederholungen ohne Analyse koennten Fehler maskieren.

## Warum wird keine automatische Wiederherstellung behauptet?
Automatische Recovery kann Seiteneffekte verschleiern. Der Plan fordert stattdessen transparente manuelle Nacharbeit und Dokumentation.

## Warum ist Failure Injection auf echter Hardware noetig?
Nur echte Hardware zeigt Timing-, Medien- und Zustandswechsel realistisch genug, um Fehlerpfade belastbar zu validieren.

## Warum laeuft jeder Failure Case einzeln?
Einzelfaelle verhindern Ueberlagerung von Effekten und machen Ursachen/Nachweise eindeutig auswertbar.

## Warum ist kein Retry nach Fehler erlaubt?
Wiederholungen ohne Analyse koennten inkonsistente Zustaende verdecken; zuerst muss der Zustand sauber bewertet werden.

## Warum muss das Medium nach Fehler neu bewertet werden?
Nach Fehlern kann der Medienzustand unklar sein; ohne neuen Gate-/State-Check ist keine sichere Fortsetzung moeglich.

## Warum wird keine automatische Reparatur behauptet?
Automatische Reparatur birgt das Risiko stiller Nebenwirkungen. Der Prozess bleibt absichtlich manuell und auditierbar.

## Warum ist Device-Reenumeration gefaehrlich?
Bei Reenumeration kann dasselbe Medium unter neuem Pfad erscheinen oder ein anderes Medium den alten Pfad uebernehmen.

## Warum ist /dev/sdb nicht stabil genug?
Kernel-Namen koennen sich durch Reconnect/Reihenfolge aendern und sind alleine kein verlässlicher Identitaetsnachweis.

## Warum werden Fingerprint und Realpath verglichen?
Nur der kombinierte Vergleich reduziert Verwechslungen zwischen Pfadwechsel und tatsaechlicher Medienidentitaet.

## Warum kein Retry nach Device-Wechsel?
Ein Device-Wechsel ist ein harter Bruch der Sicherheitsannahmen und erfordert neue, saubere Vorbedingungen statt Wiederholung.

## Warum blockieren mehrere aehnliche USB-Medien?
Mehrdeutigkeit bei Medienidentitaet ist ein zentrales Fehladressierungsrisiko und erzwingt daher Abbruch.

## Warum sind Hotplug-Race-Tests noetig?
Race-Zustaende entstehen zeitkritisch und koennen Guard-/Lifecycle-Annahmen verletzen, wenn sie nicht gezielt getestet werden.

## Warum sind unerwartete Mounts gefaehrlich?
Ein unerwarteter Mount-Wechsel kann Zielidentitaet und Sicherheitsannahmen kippen und muss daher fail-closed abbrechen.

## Warum ist Lock-Cleanup nach Abort Pflicht?
Haengende Locks blockieren Folgepruefungen und koennen zu inkonsistenten Zustandsinterpretationen fuehren.

## Warum kein Retry nach Race-Abbruch?
Race-Abbrueche signalisieren instabilen Zustand; Wiederholung ohne erneute Zustandsbewertung waere unsicher.

## Warum laeuft jeder Race-Case einzeln?
Nur isolierte Einzelfaelle erlauben klare Kausalitaet zwischen Trigger und beobachtetem Abort-/Block-Verhalten.

## Warum sind Rollback-Runtime-Tests noetig?
Sie pruefen, ob Abbruch-/Fehlerpfade sauber aufraeumen, ohne neue Risiken oder inkonsistente Restartefakte zu hinterlassen.

## Warum darf Audit nicht geloescht werden?
Auditdaten sind Sicherheits- und Nachweisgrundlage; sie duerfen nur gesichert/markiert, nicht entfernt werden.

## Warum keine rekursive Loeschung ohne Prefix?
Ohne harte Prefix-Grenze kann Cleanup in falsche Bereiche laufen und Systemdaten treffen.

## Warum sind Symlinks im Cleanup gefaehrlich?
Symlinks koennen Cleanup unbemerkt auf fremde Pfade umlenken und Sicherheitsgrenzen umgehen.

## Warum sind Systempfade tabu?
`/etc`, `/opt` und produktive `/var/lib`-Bereiche duerfen in diesem Testdesign niemals veraendert werden.

## Warum ist Testdesign-ready nicht lab-ready?
Testdesign-ready bedeutet nur, dass Plaene vollstaendig sind; Runtime-Nachweise auf echter Ausfuehrungsebene fehlen weiterhin.

## Welche Runtime-Tests fehlen noch?
Alle sieben manuellen Runtime-Ausfuehrungen zu Sudoers, Privileged Validation, Real-Write E2E, Failure Injection, Reenumeration, Hotplug-Race und Rollback.

## Warum ersetzt Plan-Doku keine Runtime-Evidence?
Dokumentation beschreibt Soll-Verhalten, beweist aber nicht das reale Verhalten unter Laufzeitbedingungen.

## Warum erfolgt keine automatische Freigabe?
Freigabe erfordert manuelle, kontrollierte Runtime-Belege; Automatik waere fuer diese Sicherheitsstufe ungeeignet.

## Warum ein zentrales Runbook-Bundle?
Ein zentrales Bundle verhindert Luecken zwischen Einzelplaenen und schafft eine nachvollziehbare, einheitliche Ausfuehrungsgrundlage.

## Warum feste Reihenfolge?
Die Reihenfolge minimiert Folgerisiken und stellt sicher, dass spaetere Schritte nur auf validierten Vorbedingungen laufen.

## Warum eine Operator-Checklist?
Kritische Sicherheitsvoraussetzungen werden aktiv bestaetigt, statt stillschweigend vorausgesetzt.

## Warum keine automatische Ausfuehrung?
Runtime-Pruefungen auf Hardware benoetigen situative menschliche Entscheidungen und kontrollierte Stop-Kriterien.

## Warum pro Runbook eigene Evidence?
Jeder Schritt hat eigene Risiken; getrennte Nachweise sind noetig, um Ursachen und Freigabestatus sauber zu belegen.

## Warum ein Runbook-Export?
Der Export macht die manuelle Durchfuehrung reproduzierbar, weil alle benoetigten Artefakte zentral und versioniert vorliegen.

## Warum ein Evidence-Template?
Ein einheitliches Template reduziert Auslassungen und verbessert Vergleichbarkeit zwischen Runbook-Laeufen.

## Warum ein JSON-Schema?
Das Schema erzwingt Pflichtfelder fuer Ergebnisdateien und erleichtert konsistente Auswertung.

## Warum kein automatischer Testlauf?
Die Runtime-Schritte bleiben bewusst manuell, da Hardwarezustand und Sicherheitsentscheidungen situativ bewertet werden muessen.

## Warum nur Docs-/Evidence-Pfade?
Exports duerfen keine Systempfade beruehren; dadurch bleiben Installation und Laufzeitumgebung unveraendert.

## Warum werden Runtime-Ergebnisdateien validiert?
Damit manuelle Lab-Ergebnisse strukturiert, vergleichbar und fail-closed ausgewertet werden koennen, bevor eine Entscheidung dokumentiert wird.

## Warum wird die Runbook-Reihenfolge geprueft?
Spaetere Hardware-/Rollback-Schritte duerfen nur auf validierten Vorbedingungen aufbauen; Out-of-order wuerde Sicherheitsaussagen entwerten.

## Warum blockiert missing evidence?
Fehlende Nachweise verhindern belastbare Sicherheitsbewertung (z. B. Mount-/Verify-/Audit-Zustand) und muessen deshalb blockierend behandelt werden.

## Warum ist lab_ready_candidate keine automatische Freigabe?
`lab_ready_candidate` ist nur eine manuelle Abnahmeentscheidung nach vollstaendiger Evidence-Pruefung, kein automatischer Execute-Trigger.

## Warum ist Pfadschutz beim Ergebnisimport noetig?
Ohne festen Allowed-Root koennten Fremdpfade, Symlinks oder Traversal unbeabsichtigt gelesen werden und den Sicherheitsrahmen umgehen.

## Warum ist lab_ready_candidate keine Produktionsfreigabe?
`lab_ready_candidate` beschreibt nur einen kontrollierten Laborstatus. Produktionsfreigaben bleiben getrennt und erfordern zusaetzliche Sicherheits- und Betriebsnachweise.

## Warum bleiben Residual Risks sichtbar?
Auch bei bestandenen Lab-Runbooks bleiben Restunsicherheiten (Scope, Host-/Medientypen, Operatorfaktoren) bestehen und muessen transparent dokumentiert werden.

## Warum bleibt die Operatorentscheidung immer erforderlich?
Die Abnahme ist bewusst manuell. Die Aggregation liefert Struktur und Hinweise, ersetzt aber keine verantwortliche Freigabeentscheidung.

## Warum blockiert ein Sicherheitsfinding?
Sicherheitsfindings zeigen verletzte Schutzannahmen (z. B. Verify-Mismatch, Device-/Mount-Drift) und muessen fail-closed zur Blockierung fuehren.

## Warum wird repeat_required nicht automatisch wiederholt?
Wiederholungen koennen Hardware-/Bedienrisiken erhoehen und brauchen daher einen expliziten, kontrollierten manuellen Neustart.

## Warum wird ein Abnahmebericht exportiert?
Der Export erzeugt nachvollziehbare, konsistente Artefakte fuer Operator-Review, Dokumentation und spaetere Audits.

## Warum ist Lab-Kandidat keine Produktionsfreigabe?
Lab-Kandidat bedeutet nur, dass die vorhandene Lab-Evidence fuer den Laborzweck ausreicht; Produktionsfreigaben brauchen zusaetzliche Nachweise.

## Warum bleiben Residual Risks im Bericht sichtbar?
Restunsicherheiten duerfen nicht verdeckt werden und muessen fuer jede manuelle Entscheidung transparent erhalten bleiben.

## Warum bleibt die Operatorentscheidung sichtbar?
Die finale Abnahme ist bewusst menschlich und nicht automatisierbar; der Bericht unterstuetzt, ersetzt aber nicht die Entscheidung.

## Warum werden JSON und Markdown erzeugt?
Markdown ist operatorfreundlich fuer Review, JSON ist maschinenlesbar fuer konsistente Weiterverarbeitung und Pruefung.

## Warum ist die Lab-Phase dokumentiert, aber nicht produktionsreif?
Die Dokumentation belegt Planung, Guards und read-only Validierung, ersetzt aber keine realen manuellen Runtime-Nachweise auf Hardware.

## Welche sieben Runtime-Tests sind noch manuell offen?
Sudoers Runtime Dry-run, Privileged Runner Validation Dry-run, Real Write Hardware E2E, Failure Injection Hardware E2E, Device Reenumeration, Hotplug/Unmount Race und Rollback Runtime.

## Warum reicht Rootless E2E nicht?
Rootless E2E validiert nur den unprivilegierten Pfad; privilegierte Runtime-, sudoers- und Hardware-Write-Risiken bleiben damit unbelegt.

## Warum bleibt der privilegierte Runner blockiert?
Solange keine kontrollierten manuellen Runtime-Ausfuehrungen mit belastbarer Evidence vorliegen, bleibt der privilegierte Pfad absichtlich gesperrt.

## Wann wird lab_ready_candidate moeglich?
Erst wenn die sieben manuellen Runtime-Ausfuehrungen in der vorgegebenen Reihenfolge mit vollstaendiger, konsistenter Evidence erfolgreich abgeschlossen sind.

## Warum ein Next-Phase-Gate?
Das Gate verhindert unsichere Folgeschritte und erlaubt nur klar begruendete naechste Phasen unter manueller Kontrolle.

## Warum bleibt manuelle Runtime erlaubt, aber Production blockiert?
Die Lab-Phase darf weiter validieren, aber ohne reale Produktionsfreigabe, solange privilegierte Runtime-Nachweise fehlen.

## Warum ist lab_ready_candidate keine Releasefreigabe?
`lab_ready_candidate` ist ein Review-Zustand fuer menschliche Entscheidung, kein technischer Schalter fuer Produktionsbetrieb.

## Warum bleibt automatisierter Deploy blockiert?
Automatisierte Ausfuehrung wuerde Operator-Gates und Sicherheitsstopps umgehen; diese Phase erzwingt bewusst manuelle Kontrolle.

## Warum bleiben Root-Backend und privilegierter Daemon verboten?
Beide Modelle vergroessern die Angriffsoberflaeche dauerhaft und widersprechen der One-shot-/Least-Privilege-Strategie.

## Warum ein Precheck vor manueller Runtime?
Der Precheck reduziert Fehlstarts, indem er Voraussetzungen, Operator-Bestaetigungen und Nachweisplanung vorab fail-closed prueft.

## Warum brauchen Dry-run-Runbooks weniger Hardwaredaten?
Dry-run-Runbooks fuehren keinen echten Write aus; deshalb sind Hardware-Details teilweise nicht anwendbar statt zwingend blockierend.

## Warum brauchen Write-bezogene Runbooks Hardware Gate und Guard?
Diese Gates sind die zentrale Schutzschicht gegen Fehlziel-/Medienrisiken vor jedem write-nahen manuellen Schritt.

## Warum sind Operator-Confirmations Pflicht?
Physische Identifikation, Backup-Status und Stop-Awareness sind nicht automatisierbar und muessen explizit bestaetigt werden.

## Warum startet der Precheck keine Ausführung?
Der Precheck ist strikt read-only und dient nur als Entscheidungsgrundlage, nicht als Trigger fuer Runtime-Aktionen.

## Warum werden Ergebnisdateien vorab erzeugt?
Vorgefertigte Templates reduzieren Auslassungen und schaffen konsistente, spaeter validierbare Runtime-Nachweise.

## Warum nur der allowed runtime-results Pfad?
Ein fester Allowed-Root verhindert Pfadmissbrauch, Traversal und unbeabsichtigte Schreibziele ausserhalb des Evidence-Bereichs.

## Warum keine automatische Befuellung?
Die Runtime-Ergebnisse muessen manuell und nachvollziehbar aus der realen Durchfuehrung stammen, nicht aus simulierten Auto-Werten.

## Warum muss Ueberschreiben explizit bestaetigt werden?
So werden bestehende Nachweise nicht versehentlich ersetzt; overwrite ist nur mit klarer Absicht erlaubt.

## Warum bleiben SHA256-Felder auch bei Dry-run vorhanden?
Ein einheitliches Schema vereinfacht Validierung und Vergleich; bei Dry-run bleiben diese Felder bewusst leer/null.

## Warum ein Edit-Checker vor dem Validator?
Der Edit-Checker liefert frueh menschlich lesbare Hinweise zu Luecken und Risiken, bevor der harte Ingestion-Validator fail-closed blockiert.

## Warum korrigiert der Checker nicht automatisch?
Runtime-Nachweise muessen manuell und nachvollziehbar bleiben; automatische Korrekturen koennten echte Beobachtungen verfaelschen.

## Warum sind leere Templates nur review_required?
Leere Felder bedeuten oft "noch nicht ausgefuellt". Das ist vor Ausfuehrung erwartbar und daher initial ein Review-, nicht zwingend ein Sicherheitsblocker.

## Warum blockieren failed/mismatch?
`failed` oder `verify_status=mismatch` sind harte Sicherheitsindikatoren und duerfen nicht stillschweigend zur Ingestion freigegeben werden.

## Warum wird suspicious target_device markiert?
Ein systemnahes Zielgeraetmuster erhoeht Fehlzielrisiko und muss sichtbar sein, auch wenn der Operator spaeter begruendet freigibt.

## Warum ein Bundle-Checker vor dem Validator?
Der Bundle-Checker prueft das komplette Sieben-Runbook-Set und die Sequenzlogik, bevor die Ingestion alle Dateien zusammen bewertet.

## Warum muessen alle 7 Runbooks vollstaendig sein?
Die Lab-Abnahme baut auf einer festen Kette auf; fehlende Schritte wuerden offene Risiken und keine belastbare Gesamteinschaetzung bedeuten.

## Warum ist die Reihenfolge blockierend?
Spaetere Schritte setzen die Nachweise frueherer Schritte voraus; falsche Reihenfolge zerstoert die Kausalitaet der Runtime-Evidenz.

## Warum verhindert ein failed Runbook spaetere Freigabe?
Wenn ein frueherer Schritt nicht `pass` ist, widersprechen spaetere `pass`-Ergebnisse der definierten Abhaengigkeitskette und werden fail-closed blockiert.

## Warum korrigiert der Bundle-Checker keine Dateien?
Nachweise muessen manuell und nachvollziehbar bleiben; automatische Korrekturen wuerden die Integritaet der Runtime-Evidenz untergraben.

## Warum existiert nach dem Bundle-Checker noch ein Handoff-Gate?
Der Bundle-Checker bewertet nur; das Handoff-Gate erzeugt ein separates, auditierbares Manifest und prueft Pfade erneut, bevor der Validator eingespeist wird.

## Warum erfolgt keine automatische Ingestion?
Ingestion bleibt eine bewusste manuelle oder separat geschuetzte Aktion; das Gate ersetzt weder Operator-Entscheid noch Validator-Lauf.

## Warum soll das Handoff-Manifest unveraenderlich sein?
Ein festes Manifest mit Ueberschreib-Schutz verhindert stille Umlenkung der Validator-Eingaben und erleichtert Nachvollziehbarkeit.

## Warum sind nur exakt sieben Runtime-Result-Dateien erlaubt?
Die Lab-Kette ist auf sieben Runbooks definiert; weniger oder mehr Dateien wuerden die Abnahmelogik und Sequenzannahmen brechen.

## Warum werden Pfade erneut geprueft?
Zwischen Bundle-Check und Handoff koennen Dateien fehlen oder Pfade manipuliert werden; das Gate validiert deshalb unmittelbar vor dem Manifest.

## Warum laeuft der Validator zuerst im Dry-Run?
Der Dry-Run nutzt dieselbe Ingestionslogik read-only und erzeugt nur einen Bericht, damit Abweichungen sichtbar werden, bevor echte Ingestion oder Freigaben diskutiert werden.

## Warum wird das Handoff-Manifest nicht veraendert?
Das Manifest ist die vereinbarte Uebergabereferenz; Veraenderungen wuerden die Nachvollziehbarkeit zwischen Bundle-Check und Validator-Lauf zerstoeren.

## Warum erfolgt keine automatische Ingestion?
Ingestion bleibt eine bewusst getrennte, manuell oder separat geschuetzte Aktion; der Dry-Run ersetzt sie nicht.

## Warum werden alle Pfade im Dry-Run erneut geprueft?
Zwischen Manifest-Erstellung und Validator-Lauf koennen Dateien fehlen oder Pfade korrumpieren; der Dry-Run validiert deshalb unmittelbar vor der Auswertung.

## Unterschied zwischen Handoff-Manifest und Dryrun-Bericht?
Das Manifest listet die sieben Validator-Eingabedateien als Uebergabeartefakt; der Dryrun-Bericht dokumentiert das Ergebnis des Validator-Laufs (inkl. Findings) und wird separat unter `handoff/` abgelegt.

## Warum wird ein Seal erzeugt?
Ein separates Seal-File ermoeglicht eine kryptografisch pruefbare Referenz auf den Dryrun-Report, ohne den Report selbst zu aendern.

## Warum SHA256?
SHA256 liefert einen standardisierten, vergleichbaren Fingerabdruck der Original-Report-Bytes fuer Integritaetskontrolle.

## Warum werden Reports unveraenderlich behandelt?
Unveraenderliche Quellen sind pruefbar; das Seal dokumentiert exakt diese Version, nicht eine nachtraeglich editierte.

## Warum muss der Dryrun zuerst ok sein?
Nur ein erfolgreicher Dryrun liefert eine belastbare Validator-Aussage; das Seal soll keine fehlgeschlagenen oder unklaren Laeufe festhalten.

## Warum werden Seal-Dateien indexiert?
Ein zentraler Index erleichtert Audit und Ueberblick, ohne einzelne Seal-Dateien zu aendern.

## Warum nur validator_status ok indexiert wird?
Nur konsistent als gueltig markierte Seals gehoeren in die Referenzliste; andere bleiben ausdruecklich ausgeschlossen.

## Warum werden ungueltige Seals ignoriert?
Fehlerhafte Artefakte wuerden den Index verfaelschen; sie werden gemeldet, aber nicht aufgenommen.

## Warum ist der Index read-only bezueglich Seals?
Der Index aggregiert nur Metadaten; Integritaet der Seals und Reports bleibt durch Nicht-Anfassen gewahrt.

## Warum wird Seal-Konsistenz geprueft?
Der Index kann veralten oder falsch referenzieren; das Audit vergleicht Eintraege mit dem Dateisystem und SHA256.

## Warum wird SHA256 erneut berechnet?
Nur ein frischer Hash beweist, dass der aktuelle Source-Report noch exakt der referenzierten Version entspricht.

## Warum erzeugen fehlende Reports warnings?
Fehlende Artefakte sind ein Drift-Signal, blockieren aber nicht zwingend alle Eintraege, solange mindestens einer gueltig bleibt.

## Unterschied Index vs. Konsistenz-Audit?
Der Index listet erwartete Seals; das Audit prueft, ob Dateien, JSON und Hashes zur Laufzeit noch zusammenpassen.

## Warum wird eine Timeline erzeugt?
Sie buendelt zeitlich sortiert zentrale Evidence-Dateien mit Fingerabdruecken fuer schnelle Nachvollziehbarkeit.

## Warum SHA256 pro Event?
Jeder Eintrag referenziert den exakten Dateiinhalt zum Zeitpunkt der Timeline-Erzeugung.

## Unterschied Seal vs. Timeline?
Ein Seal bescheinigt einen Dryrun-Report; die Timeline ordnet mehrere Artefakte (Dryrun, Seals, Index, Audit) zusammen.

## Warum ist die Timeline read-only?
Bestehende Artefakte bleiben unveraendert; es entsteht nur ein neues Aggregat.

## Warum ein Final-Snapshot der Timeline?
Er fasst die Timeline-Datei mit SHA256 zusammen und fixiert so den Nachweis-Zustand ohne andere Dateien anzufassen.

## Was bedeuten timeline_sha256 und snapshot_sha256?
`timeline_sha256` bezieht sich auf die Rohbytes der Timeline-Datei; `snapshot_sha256` signiert die Snapshot-Metadaten ohne sich selbst.

## Was macht der Final Acceptance Gate?
Er prueft den Final-Snapshot erneut gegen die Timeline-Datei (SHA256) und schreibt nur `validator_final_acceptance.json` mit dem Ergebnis (`accepted` / `review_required` / `blocked`).

## Wann ist Acceptance `review_required`?
Wenn im Snapshot-Feld `status` der Wert `review_required` steht (z. B. weil mindestens ein Timeline-Event nicht `ok` war).

## Was macht das Final Export Package?
Es liest die komplette Evidence-Kette aus `handoff/`, validiert alle JSON-Dateien und schreibt ein finales Exportpaket mit SHA256 pro enthaltener Datei.

## Wann ist der Export blockiert?
Bei `acceptance_status = blocked`, fehlenden Pflichtdateien, Symlinks, ungueltigem JSON oder Pfadverletzungen.

## Warum ist Failure-Injection noetig?
Damit Erkennungs- und Blocklogik unter realen Hardwarebedingungen reproduzierbar gegen kontrollierte Stoerfaelle validiert werden kann.

## Warum sind produktive Datentraeger verboten?
Failure-Injection darf nur auf Testmedien laufen, um reale Nutzdaten und produktive OS-Partitionen strikt zu schuetzen.

## Unterschied Simulation vs. echte Hardwaretests?
Simulation testet Modelllogik; echte Hardwaretests pruefen zusaetzlich Reenumeration, Mount-Wechsel und Berechtigungsgrenzen.

## Warum ist `destructive=false` erzwungen?
Alle Cases muessen reversibel bleiben; destruktive Operationen (z. B. mkfs/dd/wipefs) sind in diesem Modus ausgeschlossen.

## Warum nur Preview und keine automatische Ausfuehrung?
Echte Failure-Laeufe auf Hardware brauchen menschliche Kontrolle; dieses Modul erzeugt nur Planung und Operator-Anleitung.

## Warum koennen echte Hardwaretests gefaehrlich sein?
Falsche Zielmedien oder unerwartete Reenumeration koennen Datenverlust verursachen, daher strikt nur Testmedien und manuelle Schritte.

## Unterschied Matrix vs. Execution Preview?
Die Matrix definiert Fehlerszenarien; das Execution Preview leitet daraus konkrete manuelle Ablauf- und Evidence-Schritte ab.

## Warum bleibt `destructive=false` auch im Preview?
Der Preview-Mode darf nie echte Schaeden ausloesen und bleibt daher strikt reversibel und nicht-destruktiv.

## Warum sind Operator-Checklisten noetig?
Sie machen manuelle Failure-Laeufe reproduzierbar, sicher und nachweisbar, ohne automatische Eingriffe.

## Warum gibt es keine automatische Failure-Ausfuehrung?
Bei echter Hardware muss ein Operator Zielmedien, Reihenfolge und Abbruchkriterien kontrollieren.

## Warum sind Abort-Conditions wichtig?
Sie verhindern Fehlversuche auf falschen oder produktiven Datentraegern und stoppen bei Risiko sofort.

## Unterschied Preview vs. Operator-Checklist?
Das Preview beschreibt Laufplanung je Failure-Fall; die Operator-Checklist liefert konkrete Schritt-fuer-Schritt-Kontrollen inklusive Evidence-Anforderungen.

## Warum existieren Testsessions getrennt von Checklisten?
Die Checkliste ist die Referenz pro Failure-Typ; die Testsession buendelt dieselben Regeln in einen durchfuehrbaren Session-Plan mit Session-ID und Endzustands-Erwartung.

## Warum ist nur `manual_only` erlaubt?
Hardware-Failure-Tests duerfen nicht automatisch starten; der Operator muss jeden Lauf explizit einleiten und abbrechen koennen.

## Warum ist `expected_final_state` wichtig?
Damit nach einem manuellen Lauf klar ist, welche sicheren und nachweisbaren Ergebnisse gelten duerfen, ohne produktive Medien zu beruehren.

## Unterschied Checklist vs. Testsession?
Die Checkliste ist die kontrollierte Schrittliste; die Testsession ist die zeitlich geordnete Ausfuehrungsplanung inklusive Session-Kennung und Endzustandskriterien.

## Warum werden Testergebnisse getrennt gespeichert?
Sessions beschreiben den Plan; die Ergebnisdatei haelt die tatsaechlichen Beobachtungen und Evidence getrennt fuer Audit und Nachvollziehbarkeit.

## Warum werden deviations dokumentiert?
Abweichungen vom erwarteten Verhalten sind fuer Risiko- und Korrekturentscheidungen genauso wichtig wie erfolgreiche Erkennung.

## Warum ist rollback_performed wichtig?
Es zeigt an, ob nach einem Failure-Lauf ein kontrollierter Rueckbau erfolgte, ohne automatische Reparatur auszuloesen.

## Unterschied Session vs Result?
Die Session ist die geplante Testeinheit; das Result erfasst den realen Lauf (Zeit, Operator, Status, Evidence, Abweichungen).

## Warum werden Failure-Ergebnisse evaluiert?
Damit manuelle Beobachtungen gegen die Preview-Detection-Regeln und Session-Vorgaben geprueft werden, ohne erneut auf Hardware zuzugreifen.

## Warum sind mismatches wichtig?
Sie zeigen, wenn beobachteter Status vom erwarteten abweicht, und triggern Review bevor die Kette als sauber gilt.

## Unterschied Result vs Evaluation?
Das Result ist die Rohdokumentation des Laufs; die Evaluation ist die read-only Bewertung inklusive Zaehlern und Findings.

## Warum loesen deviations review_required aus?
Jede dokumentierte Abweichung bedeutet zusaetzliches Risiko oder Unklarheit und erfordert menschliche Nachpruefung.

## Warum ist ein Readiness-Gate nötig?
Es bündelt alle Failure-Artefakte und Safety-Checks, bevor echte Hardwaretests starten, ohne automatisch auszuführen.

## Warum wird destructive=false global erzwungen?
Damit in der gesamten Pipeline kein Fall als destruktiv markiert werden kann und Testmedien-Regeln klar bleiben.

## Unterschied Evaluation vs Readiness?
Die Evaluation prüft Session-Ergebnisse gegen Preview-Regeln; das Readiness-Gate prüft zusätzlich Vollständigkeit und Konsistenz aller Pipeline-Dateien.

## Warum blockieren fehlende Abort-Conditions?
Ohne dokumentierte Abbruchkriterien fehlt ein zwingender Operator-Schutz vor falschen oder riskanten Läufen.

## Warum werden Laptop-Testläufe ausgewählt?
Damit nach dem Readiness-Gate eine begrenzte, geprüfte Reihenfolge manueller Läufe festliegt, ohne automatische Ausführung oder Reparatur.

## Warum kommt Low-Risk zuerst?
Geringeres Restrisiko und weniger Operator-Belastung sollen vor mittlerem Risiko stehen, solange beides zulässig ist.

## Warum blockieren Produktivmarker?
Jede Erwähnung produktiver oder interner OS-Volumes in Sessions oder Checklisten bricht die Auswahl ab, um Daten- und Systemvolumen auszuschließen.

## Unterschied Readiness vs Run Selection?
Readiness prüft Vollständigkeit und globale Safety der Pipeline-Artefakte; die Run Selection filtert und sortiert daraus einzelne manuelle Sessions für die nächsten Laptop-Schritte.

## Warum ist eine Operator-Runorder nötig?
Damit die ausgewählten Läufe in einer festen, wiederholbaren Reihenfolge abgearbeitet werden können, ohne Automatik und ohne Medien-/Mount-Risiken zu vermischen.

## Warum kommen ungefährliche Fälle zuerst?
Runs ohne Medien- und Mount-Wechsel sowie ohne Rollback-Last reduzieren Kontextwechsel und Restrisiko vor anspruchsvolleren Schritten.

## Unterschied Selection vs Runorder?
Die Selection liefert die zulässige Teilmenge und eine Sortiergrundlage; die Runorder bildet daraus eine explizite Operator-Schrittliste inkl. Gruppierung.

## Warum steht medium risk zuletzt?
Höhere Bewertung soll erst nach niedrigerem Risiko und stabilerem Setup folgen, damit Operator und Umgebung vorbereitet sind.

## Warum braucht man ein leeres Execution-Log-Template?
Damit jeder manuelle Lauf dieselben Pflichtfelder hat und Ergebnisse vergleichbar dokumentiert werden, ohne automatische Ausfuehrung.

## Unterschied Runorder vs Execution-Log?
Die Runorder legt die Schrittfolge fest; das Execution-Log protokolliert pro Schritt den real beobachteten Verlauf.

## Warum braucht man eine Execution-Log-Validierung?
Damit nur vollstaendige und konsistente manuelle Eintraege in der Nachweis-Kette weiterverwendet werden.

## Wann ist die Execution-Log-Validierung review_required?
Wenn Abweichungen dokumentiert sind, `observed_status` auf `review_required` steht oder ein Abort ausgelöst wurde.

## Wofuer dient das Laptop-Failure-Test-Summary?
Es verdichtet die Validierung auf Gesamtstatus, Run-Zaehler und Findings fuer einen schnellen manuellen Entscheidungsblick.

## Wofuer dient der Laptop-Failure-Final-Report?
Er liefert den finalen manuellen Status samt Empfehlung (`proceed`, `review_before_next_run`, `blocked`) und bindet die Summary per SHA256 eindeutig.

## Wofuer dient das Final-Export-Package?
Es buendelt Final-Report, Summary, Validation und Execution-Log in einer referenzierbaren Paketdatei inkl. SHA256 je Artefakt.

## Wofuer dient die Laptop-Failure-Evidence-Timeline?
Sie ordnet alle Laptop-Failure-Artefakte chronologisch und ergaenzt SHA256 pro Eintrag fuer die Nachvollziehbarkeit.

## Unterschied Timeline, Snapshot, Acceptance und Export?
Timeline ordnet Artefakte zeitlich; Snapshot fixiert den Timeline-Stand mit Hash; Acceptance bewertet den Snapshot; Export/Finalized Export buendelt Artefakte fuer nachvollziehbare Weitergabe.

## Warum erfolgt kein automatischer Release?
Die Kette bleibt strikt read-only und manuell, damit keine Freigabe ohne explizite menschliche Entscheidung ausgelöst wird.

## Warum werden Hashes vor Export erneut geprüft?
Damit Integritaet und Referenzierbarkeit aller relevanten Artefakte vor dem finalen Paket erneut verifiziert sind.

## Warum ist review_required nicht accepted?
`review_required` bedeutet offener manueller Pruefbedarf und darf daher nicht als akzeptierter Abschluss behandelt werden.

## Warum erhöhen STRICT-Phasen die Version?
Jede abgeschlossene STRICT-Phase muss eindeutig in der Historie sichtbar sein, damit Evidence, Tests und Entwicklungsstand sauber zugeordnet werden können.

## Unterschied Patch/Minor/Major?
Patch steht fuer kleine Fixes/Doku, Minor fuer neue STRICT-Module und Pipelines, Major fuer Architektur- oder Plattformspruenge.

## Warum werden interne Teststufen versioniert?
Auch `internal_testing` ist ein verbindlicher Meilenstein und soll reproduzierbar mit Version und Artefakten verknuepft sein.

## Warum gibt es keine automatischen Releases?
Version-Governance dient nur Tracking und Konsistenzpruefung; Releases bleiben bewusst manuell freizugeben.

## Warum ist eine zentrale Versionsquelle nötig?
Damit Frontend, Backend, API, Tauri und Evidence dieselbe Projektversion nutzen und keine Drift entsteht.

## Warum sind hardcodierte Versionen gefährlich?
Sie führen zu widersprüchlichen Ständen in UI, API und Artefakten und erschweren Diagnose sowie Abnahme.

## Unterschied Version Governance vs Source of Truth?
Governance regelt wann wie gebumpt wird; Source of Truth legt fest, welche Datei die kanonische Version liefert.

## Warum erzeugt das keine automatischen Releases?
Die Mechanik aktualisiert nur Metadaten und Checks, nicht aber Tags, Publish- oder Deploy-Schritte.

## Warum wird pi-installer aus aktiven Identifikatoren entfernt?
Damit Runtime-Pfade, Services, ENV-Namen und App-Identifier eindeutig unter Setuphelfer konsolidiert sind.

## Warum bleiben historische Nachweise erhalten?
Evidence, historische Doku und Changelog-Eintraege sind fuer Auditierbarkeit und Rueckverfolgbarkeit notwendig.

## Unterschied Legacy vs Active Runtime?
Legacy ist nur dokumentierte/deprecated Kompatibilitaet; Active Runtime sind produktive Identifier und duerfen kein pi-installer mehr enthalten.

## Warum sind Alias-Kompatibilitaeten noetig?
Sie erlauben kontrollierte Uebergangsfaelle im Read-only-Modus ohne harte Runtime-Brueche.

## Warum erfolgt kein Blind-Replace?
Jede Datei wird klassifiziert; nur `rename_now` unter erlaubten Projekt-Pfaden darf automatisch geschrieben werden, damit Evidence und Historie unveraendert bleiben.

## Warum bleiben historische pi-installer-Nachweise bestehen?
Evidence, Changelog und Historie sind Audit-Pfade und werden bewusst nicht ueberschrieben.

## Warum werden Legacy-Backups erzeugt?
Vor jedem kontrollierten Rewrite sichert das Tool den Originaltext unter `handoff/legacy-backups/`, damit ein Rollback ohne Git moeglich ist.

## Warum existieren alte Aliases noch read-only?
Lesende Kompatibilitaet verhindert Brueche bei Umgebungen, die noch alte ENV-Namen setzen, ohne neue Legacy-Schreibwege einzufuehren.

## Warum nur 100 Aenderungen pro Cleanup-Zyklus?
Kleine Batches reduzieren Risiko, erleichtern Review und halten Backups sowie Diffs beherrschbar.

## Warum erfolgt Cleanup schrittweise?
Nach jedem Zyklus folgen erneutes Inventory und Consistency-Check; so bleibt die Lage messbar und Evidence/Historie bleiben geschuetzt.

## Warum wird nach jedem Zyklus erneut gescannt?
Nur so laesst sich Drift und verbleibende aktive Legacy-Identifier zuverlaessig zaehlen und fuer den naechsten Zyklus planen.

## Warum bleibt die Version bei 1.7.0?
Reine Identifier-Bereinigung innerhalb derselben Phase erfordert keinen weiteren SemVer-Bump.

## Warum sind Hotspot-Analysen nötig?
Sie gruppieren Treffer nach Wirkungsort (Backend, Tauri, ENV, Skripte, Packaging, Tests), damit Cleanup gezielt und risikobewusst geplant wird statt nur eine Rohtrefferzahl zu sehen.

## Warum sind Runtime-Identifier kritischer als Kommentare?
Runtime-Identifier wirken auf Pfade, Dienste, Umgebungsvariablen, APIs und Builds; Kommentare sind meist dokumentarisch und verursachen keine aktive falsche Systemkonfiguration.

## Warum löst ein Unknown-Identifier `review_required` aus?
Ohne Zuordnung zu einem bekannten Cluster ist nicht abschätzbar, ob es sich um produktiven Code, Konfiguration oder nur Doku handelt — manuelle Einordnung ist Pflicht.

## Warum werden Tests zuletzt bereinigt?
Produktiver Code, Startskripte und Packaging beeinflussen das reale Systemverhalten; Testdateien folgen, sobald die Laufzeitpfade stabil sind.

## Warum ist Cleanup Cycle 2 hotspot-basiert?
Damit nur die in der Hotspot-Analyse priorisierten Pfade mit dem sicheren Rewrite-Plan abgeglichen werden — ohne flaechendeckendes Blind-Replace.

## Warum werden in Cycle 2 nur critical/high bereinigt?
Mittlere und niedrige Treffer sind absichtlich weniger dringlich und bleiben fuer spaetere, kleinere Runden oder manuelle Nacharbeit.

## Warum werden Unknown-Cluster nicht automatisch geaendert?
Ohne klare Einordnung waere das Risiko nicht steuerbar; Unknown bleibt fuer manuelle Klassifikation reserviert.

## Warum hoechstens 50 Aenderungen pro Hotspot-Cycle?
Die Grenze haelt Diffs, Backups und Review-Aufwand beherrschbar und reduziert Fehlerrisiko bei produktiven Pfaden.

## Unterschied Cleanup-Zyklus vs Runtime-Elimination?
Cleanup-Zyklen (1/2) arbeiten batchweise mit festen Caps; **Runtime-Elimination** baut explizit Targets aus Hotspot/Consistency, kreuzt mit dem Safe-Plan und schreibt nur klar erlaubte Produktivpfade.

## Warum werden Runtime-Identifier zuerst entfernt?
Sie wirken auf ENV, Installationspfade, Units und App-IDs — das ist das reale Laufzeitrisiko, nicht Kommentar- oder Dokuzeilen.

## Warum bleiben Legacy-Aliases read-only?
Damit alte Bezeichner dokumentiert und kompatibel bleiben, ohne neue pi-installer-Schreibpfade einzufuehren.

## Wann ist ein Patch-Bump auf 1.7.1 erlaubt?
Nur wenn der Elimination-Postcheck meldet, dass keine aktiven Runtime-Identifier mehr existieren, critical/high in der Hotspot-Analyse null sind und der Identifier-Consistency-Check nicht **blocked** ist — dann wird **1.7.1** nur als Empfehlung vorbereitet, ohne automatische Versionsdatei-Aenderung.

## Warum Zero State vor Version 1.7.1 noetig ist?
Die Zero-State-Verifikation buendelt Inventory, Hotspot, Consistency und Alias-Vertrag — ohne gruenes Ergebnis waere ein Versionsprung nicht belegt.

## Warum erfolgt der Patch-Bump nicht automatisch?
`no_auto_apply` und das explizite Apply-Flag halten SemVer und Evidence bewusst in menschlicher Freigabe.

## Warum duerfen Alias-Reste erlaubt sein?
Read-only-Kompatibilitaet in `compatibility_aliases.json` und Historie ist gewollt, solange keine aktiven Produktivtreffer mehr existieren.

## Warum blockieren Runtime-Reste?
Jeder verbleibende PI_INSTALLER-/Pfad-/Service-/App-Identifier ausserhalb erlaubter Kontexte widerspricht dem Ziel „Elimination abgeschlossen“.

## Warum ist pi-installer ab jetzt in Runtime verboten?
Der Branding-Guard soll verhindern, dass alte Produktnamen erneut in Code, Config, ENV oder Packaging landen — Setuphelfer ist die einzige Runtime-Marke.

## Warum bleiben historische Nachweise erhalten?
Evidence-, History- und Migrationspfade sowie `compatibility_aliases.json` duerfen Legacy zeigen, ohne den Guard zu verletzen.

## Warum veraendert der Guard keine Dateien?
Nur Pruefung und Evidence-JSON — kein Rewrite, damit keine heimlichen Textaenderungen neben dem Review-Prozess entstehen.

## Warum ist Setuphelfer jetzt die einzige Runtime-Marke?
Ein eindeutiger Marken- und Pfadraum reduziert Supportfehler, Doppelinstallationen und falsche systemd-/App-IDs.

## Was passiert mit alten pi-installer-Installationen?
Die Legacy-Runtime-Kompatibilitaets-Pipeline wertet nur Handoff-/Evidence-Daten aus und erzeugt Inventar, Koexistenz-Analyse und Empfehlungen — ohne echte Migration auf dem Zielsystem.

## Warum werden alte Configs nicht geloescht?
Loeschbefehle waeren irreversibel und ausserhalb des Review-Prozesses; stattdessen werden Archivierung, Read-only und Disable empfohlen.

## Warum kann Koexistenz problematisch sein?
Doppelte Services, Desktop-Eintraege oder parallele Pfade koennen Ports, ENV und Backups gegeneinander laufen lassen — die Analyse markiert solche Konflikte.

## Warum wird disable statt delete empfohlen?
`systemctl disable` (manuell, nach Freigabe) haelt Rollback- und Datenoptionen offen; Delete waere fuer Altinstallationen oft zu riskant.

## Was ist der Laptop Live Probe Handoff?
Ein dreiteiliger Ablauf (Plan, read-only Execute, Final-Gate), der nur HTTP-Lesevorgaenge gegen das Backend ausfuehrt — ohne Restore, ohne echte Verify-Pfade ohne explizites Flag.

## Warum braucht Execute ein explizites Flag?
Damit niemand versehentlich Live-Anfragen ausloest; `explicit_execute_live_probe=true` ist die bewusste Freigabe.

## Warum blockiert Legacy in API-Antworten?
Wenn pi-installer-/PI_INSTALLER-Strings in JSON-Antworten auftauchen, widerspricht das dem Setuphelfer-Branding-Ziel — das Final-Gate bleibt blockiert.

## Warum Debian Live als Basis fuer den Rettungsstick?
Stabile Paketbasis, breite Hardwareunterstuetzung, gute Passung zum Python/apt-Setuphelfer-Stack und planbare Wartung — siehe Architektur `docs/rescue/SETUPHELFER_RESCUE_STICK_ARCHITECTURE_DE.md` und Live-OS-Handoff `rescue_live_os_base_decision.json`.

## Warum wird noch kein USB geschrieben?
Die Phase erzeugt nur Architektur, Gates und Build-Vorbereitung; USB-Flash (`dd`) bleibt hinter einem spaeteren, separaten Gate und der Build-Safety-Policy (`docs/developer/RESCUE_STICK_BUILD_SAFETY_POLICY.md`).

## Warum ist Restore vom Stick zunaechst nur Preview?
Automatischer Restore waere destruktiv und braucht eigene Sessions, Tokens und Hardware-Gates — der MVP-Strang erlaubt nur Analyse, Verify und Preview.

## Warum Raspberry Pi erst spaeter getestet wird?
amd64-UEFI-Laptops sind der erste Kontrollpfad; ARM/RPi braucht eigene Images, Firmware und Testmatrix-Eintraege unter `later`.

## Warum ist Secure Boot zunaechst review_required?
Shim/Signatur, Firmware-Verhalten und Testhardware sind noch nicht Bestandteil des automatischen OK-Gates — die Bewertung steht explizit in der Live-OS-Entscheidung und der ISO-Testmatrix (`later`).

## Warum zunaechst nur VM fuer den Rescue-ISO-Test?
Kontrollierbare Umgebung, Snapshots, kein Risiko fuer produktive Host-Platten und klare NAT-Anbindung — siehe `docs/developer/RESCUE_VM_TEST_SAFETY_POLICY.md`.

## Warum bleibt die Runtime-Probe readonly?
Restore-Execute und echte Schreibpfade bleiben gesperrt; HTTP-Checks (Version, Health, Inspect, Branding) reichen fuer Phase-1-Abnahme.

## Warum noch kein echter USB-Stick?
`dd` und USB-Flash sind weiterhin ausserhalb der Gates; ISO liegt nur unter `build/rescue/output/`.

## Warum keine automatische Wiederherstellung?
Wiederherstellung bleibt bewusst manuell/sessiongebunden; der ISO-Strang validiert nur Erreichbarkeit und Sicherheit.

## Warum weiterhin Debian Live fuer den Build?
Stabile Basis, live-build-Tooling und Ueberinstimmung mit dem bestehenden Setuphelfer-Stack — siehe `docs/deploy/DEPLOY_RESCUE_ISO_BUILD_AND_VM_VALIDATION_DE.md`.

## Warum readonly Mounts im Rescue-Live-Lauf?
Jede Schreiboperation auf internen Systemplatten ist destruktiv und schwer rueckgaengig; readonly Mounts erlauben Inspektion (EFI, Root, Backups) ohne Datenveraenderung — siehe `docs/deploy/DEPLOY_RESCUE_LIVE_RUNTIME_AND_STORAGE_VALIDATION_DE.md`.

## Warum keine automatische EFI-Reparatur?
Firmware, NVRAM und Bootloader sind fehleranfaellig; automatische Reparaturen koennten unbootbar machen. Diese Phase liefert nur Analyse und Gates.

## Warum kein Restore direkt vom Stick?
Restore ist session- und tokengebunden und braucht explizite Ziele; der Stick-Strang bleibt bei Discovery, Preview und Safety.

## Warum externe Evidence-Ziele empfohlen werden?
Im RAM-Live-System gehen Logs bei Reboot verloren; Export auf USB oder ein separat gewaehltes Ziel ausserhalb der Systempartition sichert Nachweise — ohne implizites Ueberschreiben von Systemdaten.

## Warum SSH nicht automatisch aktiviert wird?
Offene Fernzugriffe erhoehen das Angriffsfenster; Remote-Hilfe bleibt Plan-only, bis ein Operator SSH bewusst startet — siehe Remote-Help-Handoff und Safety-Gate.

## Warum nur Restore Preview?
Echte Restore-Writes sind irreversibel und brauchen eigene Execute-Gates; die Simulationsphase listet nur betroffene Pfade, Mounts und Risiken — siehe `docs/deploy/DEPLOY_RESCUE_RECOVERY_SIMULATION_AND_HARDWARE_VALIDATION_DE.md`.

## Warum readonly Recovery?
Interne Systemplatten duerfen in dieser Phase nicht beschrieben werden; Zielvalidierung, Mounts und Preview bleiben analysebasiert.

## Warum Hardwaretests noetig sind?
VM und synthetische Handoffs reichen nicht fuer Firmware, NVMe, WLAN und reale USB-Mounts; die Hardware-Testkette dokumentiert den erwarteten Ablauf auf Referenzgeraeten.

## Warum Backup-Verify zwingend ist?
Ohne Manifest/SHA256-Kette waere eine Restore-Preview unsicher; Verify erkennt beschaedigte oder inkonsistente Archive vor jeder spaeteren Write-Phase.

## Warum noch keine echte ISO gebaut wird?
Die Readiness-Pipeline erzeugt nur JSON-Handoffs, Scans und Gates; ein echtes Image bleibt einem separaten, explizit freigegebenen Build-Schritt vorbehalten — siehe `docs/deploy/DEPLOY_RESCUE_ISO_READINESS_PIPELINE_DE.md`.

## Warum Debian Live genutzt wird?
Stabile Paketbasis, live-build-Tooling und gute Passung zum bestehenden Setuphelfer-Stack.

## Warum readonly Recovery zuerst kommt?
Schreiboperationen auf Systemplatten sind riskant; Preview- und Verify-Stränge laufen vor jeder spaeteren Execute-Phase.

## Warum kein Auto-Restore erlaubt ist?
Restore ist destruktiv und erfordert Sessions, Tokens und Zielprüfungen — keine stillen Automatismen in der ISO-Readiness-Pipeline.

## Warum zeigt der Rettungsstick erst eine Restore-Vorschau?
Der Stick orchestriert in Phase C.4 nur einen **Preview-Plan** (`build_rescue_restore_preview_plan`). Die kanonische Engine `modules.rescue_restore_dryrun` wird referenziert, aber nicht automatisch ausgeführt. Details: `docs/rescue-stick/RESCUE_RESTORE_PREVIEW_HANDOFF_2026-05-20.md`.

## Warum wird nicht sofort wiederhergestellt?
`execution_allowed` bleibt **false**. Es gibt keine Route `restore/start` oder `restore/run` im C.4-Strang. Erst nach expliziter Freigabe, Verify und Backup-before-overwrite kann eine spätere Execute-Phase folgen.

## Warum muss ein Ziel mit vorhandenen Daten zuerst gesichert werden?
`core/backup_before_write_gate` setzt bei erkannten Dateisystemen, OS- oder Nutzerdaten `backup_required: true`. Ohne Evidence ist der Preview-Plan **blocked** oder **required** — kein stilles Überschreiben.

## Warum reicht ein Operator-Override nicht als sichere Datensicherung?
Override liefert höchstens `review_required`, nie automatisch `satisfied`. Es dokumentiert eine bewusste Entscheidung, ersetzt aber kein Backup des Ziels.

## Warum muss Verify vor Restore erfolgen?
Profil `offline-full-restore-preview` verlangt `requires_verify_before_restore`. `verify_status: failed` blockiert den Plan; `unknown` führt zu `review_required`.

