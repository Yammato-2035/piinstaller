# FAQ – Rescue / Bootstick (Phase 0–3)

## Was ist der Rescue-Stick?

Ein geplantes **minimales Bootsystem** mit Setuphelfer-**Read-only-Diagnose** (siehe `docs/architecture/RESCUE_BOOT_ARCHITECTURE.md`). Phase 0/1 liefern Konzept + Analyse; **Phase 2** ergänzt **Restore-Dry-Run** ohne echtes Überschreiben; **Phase 3** erlaubt einen **kontrollierten echten Restore** nur mit Dry-Run-Token, Bestätigungen und erlaubten Zielpfaden.

## Macht die Diagnose Änderungen an meiner Platte?

**Nein** — bewusst keine Schreibzugriffe auf erkannte Systemlaufwerke, kein Restore, kein automatisches Schreib-Mount. `fsck` und `xfs_repair` laufen nur mit **`-n`** und nur, wenn das Ziel **nicht** gemountet ist.

## Was macht der Restore-Dry-Run?

- Prüft Backup-Pfade (Allowlist), Archiv-Inhalt (Symlink-/Pfadregeln wie bei Restore/Verify), optional Zielplatte.
- Schreibt **nur** in Sandbox unter `/tmp/setuphelfer-rescue-dryrun-staging/…` für `verify_deep`.
- **Kein** `dd`, **kein** Bootloader-Write, **kein** Root-Overwrite.

**Hinweis (FIX-1):** Produktionsnahe Backups liegen unter **`/mnt/setuphelfer/backups`** (Gruppe `setuphelfer`, 0770). Rescue liest weiterhin aus den dokumentierten Backup-Lesepfaden; Schreib-Sandbox bleibt unter `/tmp/…`.

Typische Fehlerbilder:

| Code / Bereich | Bedeutung |
|----------------|-----------|
| `rescue.dryrun.blocked_tar_entries` | Tar enthält absolute Pfade, Geräte/FIFO oder andere blockierte Mitglieder. |
| `rescue.dryrun.verify_deep_failed` | Checksummen/Manifest vs. Archiv oder Extract in Sandbox fehlgeschlagen. |
| `rescue.backup.incremental_needs_full` | Inkrementelles Archiv ohne belastbares Vollbackup für Komplett-Restore. |
| `rescue.target.capacity_insufficient` | Geschätzter Umfang passt nicht auf das Ziel-Blockgerät. |

## Bedeutung GREEN / YELLOW / RED (Dry-Run)

- **GREEN**: Backup ok, Sandbox-Dry-Run ok, Boot-Heuristik „wahrscheinlich ok“, keine roten Blocker.
- **YELLOW**: z. B. nur `analyze_only`, Boot unsicher, SMART-Warnung, oder verschlüsseltes Backup mit „Schlüssel vorhanden“-Flag ohne echte Entschlüsselung.
- **RED**: blockierter Dry-Run, kaputtes Backup, fehlendes Schlüsselflag bei `.gpg`, oder Zielplatte SMART-kritisch / zu klein (Empfehlung neue Platte).

## Warum kann trotz Backup „kein Restore“ empfohlen werden?

- Archiv beschädigt oder nicht verifizierbar.
- Inkrementell ohne Vollbasis.
- Archiv-Inhalt verletzt Sicherheitsregeln (blockierte Einträge).

## Wann wird eine **neue Zielplatte** empfohlen?

Wenn die Kapazität für den geschätzten Restore nicht reicht oder SMART einen kritischen Zustand meldet (`restore_decision`: `recommend_new_target_disk`).

## Wann **Datenrettung zuerst**?

Wenn das Backup als **korrupt** eingestuft wird (`recommend_data_recovery_first`) — klassischer Restore würde wahrscheinlich nichts Nützliches bringen.

## Wo liegen die Berichte?

- Read-only-Analyse: `/tmp/setuphelfer-rescue-report.json` (und `.md`).
- Restore-Dry-Run: `/tmp/setuphelfer-rescue-dryrun.json` (und `.md`).

## Gibt es Deutsch und Englisch?

Ja. Die API liefert nur **Codes**; Texte kommen aus `frontend/src/locales/de.json` und `en.json`.

## Was macht Phase 3 (echter Restore)?

- Nur nach erfolgreichem **Dry-Run** (`dryrun_mode=dryrun`, `DRYRUN_OK`) mit zeitlich begrenztem **Token** unter `/tmp/setuphelfer-rescue-dryrun-state/` (Details: `docs/rescue/RESTORE_EXECUTION.md`).
- **RED**-Risiko oder unpassende `restore_decision` → kein Start; bei **YELLOW** zusätzlich `risk_acknowledged: true`.
- Ziel nur unter definierten Live-Präfixen; **leeres** Verzeichnis; **kein** Überschreiben des laufenden Root-Blockgeräts; Mount muss zum gewählten `target_device` passen (falls gesetzt).
- Optional **AES-Schlüssel** (Hex) für Setuphelfer-interne verschlüsselte Container; falsche Schlüssel → Abbruch mit Code `rescue.restore.RESTORE_KEY_INVALID`.
- Log: `/tmp/setuphelfer-rescue-restore.log`; Audit: `/tmp/setuphelfer-rescue-restore-report.json` und `.md` (Stages, Hard-Stops, Session, **keine** Secrets).
- **`session_id`**: stets aus Dry-Run-JSON übernehmen; bei Remote-Login muss dieselbe Session den Restore ausführen, wenn der Grant `session_source: remote_db` trägt.
- Boot-Reparatur nur explizit (`perform_boot_repair`) und nur mit Blockgerät — modular dokumentiert in `docs/rescue/BOOT_REPAIR.md` und `docs/rescue/BOOT_COMPATIBILITY_LIMITATIONS.md`.
- Zielidentität (Seriennummer/UUID/Größe) wird mit Dry-Run verglichen — schützt vor vertauschten `/dev/sdX`-Namen.

## Warum lief mein Backup, aber das System ist nach Restore trotzdem nicht nutzbar?

Ein erfolgreiches Archiv ist nur ein Teilkriterium. Entscheidend ist der Zielzustand: Dienste muessen starten, Pfade/Berechtigungen muessen stimmen und Boot muss reproduzierbar funktionieren.

## Warum startet der Dienst nach Restore nicht?

Typische Ursachen sind systemd-Restriktionen, fehlende Runtime-Variablen (z. B. `NODE_OPTIONS`), falsche Berechtigungen oder Port-Konflikte.

## Warum reicht ein erfolgreiches Archiv allein nicht aus?

Weil Integritaet des Backups nicht automatisch bedeutet, dass die Zielumgebung konsistent ist. Setuphelfer bewertet daher Verify, Restore-Validierung und Runtime-Status zusammen.

## Warum verwendet Setuphelfer eine Gruppe statt manuellem `chown`?

Das Gruppenmodell (`setuphelfer`, `0770`, `SupplementaryGroups`) ist reproduzierbar und weniger fehleranfaellig als ad-hoc `chown`-Workarounds.

## Warum sichert `type=data` nicht alle Systempfade?

`type=data` ist bewusst als **nicht-privilegierter** Modus ausgelegt (kein sudo im Tar-Pfad, `NoNewPrivileges=true` bleibt aktiv). Deshalb werden root-only/systemnahe Quellen nicht pauschal mitgenommen.

Wenn ein Data-Lauf auf nicht lesbare Quellen trifft, liefert die API strukturiert `backup.source_permission_denied` (Diagnose `BACKUP-SOURCE-PERM-032`) statt eines unklaren Tar-Rohfehlers. Für vollständige System-/Container-Daten ist ein anderer Backup-Typ nötig.

## Warum scheitert ein Backup mit „Keine Berechtigung“, obwohl das Ziel beschreibbar ist?

Dann liegt das Problem meist an den **Quellpfaden**, nicht am Zielpfad. Beispiel: Ziel unter `/mnt/setuphelfer/backups/...` ist korrekt beschreibbar, aber `type=data` versucht zusätzlich Quellen zu lesen, die im Dienstkontext nicht zugreifbar sind. Ergebnis: `backup.source_permission_denied` / `BACKUP-SOURCE-PERM-032`.

## Warum ist `type=data` nicht dasselbe wie Full-System-Backup?

`type=data` ist ein nicht-privilegierter, reproduzierbarer Modus für Nutz-/Projektdaten im Dienstkontext. Full-/System-/Container-Bereiche gehören in einen anderen Modus und sind bewusst nicht Teil von `type=data`.

## Warum kann eine alte Installation auf Port 8000 Tests verfälschen?

Wenn auf `127.0.0.1:8000` ein alter Dienst (z. B. alte `pi-installer`-Runtime) antwortet, laufen API-Tests gegen den falschen Code-Stand. Dann sind Ergebnisse zu FIXes (z. B. FIX-2/FIX-3) nicht belastbar, auch wenn der aktuelle Repo-Stand korrekt ist.

## Warum scheitert Restore auf `/tmp`?

`/tmp` ist haeufig `tmpfs` und damit speicherbegrenzt. Fuer groeßere Backups fuehrt das zu Platzproblemen.

## Warum erkennt die Diagnose mehrere Ursachen?

Der Matcher kann Primaerdiagnose plus Nebenbefunde liefern, wenn mehrere starke Signale gleichzeitig vorliegen.

## Was bedeutet niedrige Confidence?

Niedrige Confidence bedeutet: Es gibt nur schwache Evidenz, meist Symptom statt belastbarer Root-Cause. Weitere Checks sind erforderlich.

## Warum sammeln wir System- und Laufwerksdaten?

Damit Fehler reproduzierbar einem Hardware-/Boot-/Storage-Kontext zugeordnet werden koennen. Ohne diesen Kontext bleiben viele Diagnosen unscharf.

## Warum reicht ein Fehlertext allein nicht?

Ein einzelner Fehlertext ist oft nur ein Symptom. Fuer belastbare Ursachen braucht es Signale, Umgebungskontext und den realen Testausgang.

## Warum lernt das System nicht blind automatisch?

Weil unkontrolliertes Lernen Fehlannahmen verfestigt. Neue Evidenz wird strukturiert erfasst und nachvollziehbar in Katalog/Regeln/Testfaelle rueckgefuehrt.

## Warum muessen Symptome und Root-Cause getrennt erfasst werden?

Damit falsche Erstannahmen sichtbar bleiben und spaeter korrigiert werden koennen. Das verhindert, dass der Diagnosekatalog Symptome mit Ursachen verwechselt.

## Warum ist der isolierte Raspberry-Pi-Test nicht sofort freigegeben?

Vor dem Pi-Haupttest muessen Wechselmedienpfade (externe NVMe, USB-Stick, SD-Karte) unter kontrollierten Bedingungen abgedeckt sein. Ohne diese Vorstufe waere die Ursache bei Fehlern nicht sauber eingrenzbar.

---

## Backup & Verify (HW1-03) — häufige Fragen (DE)

### 1. Warum schlägt Verify fehl, obwohl das Backup existiert?

Die Datei kann vorhanden sein, aber **Verify (besonders `mode=deep`)** prüft mehr als die Existenz: **MANIFEST.json**, **SHA-256** je Datei und die **Lesbarkeit** von gzip/tar. Fehlt das Manifest, sind Checksummen falsch oder ist das Archiv beschädigt, liefert die API z. B. `backup.failed_manifest_missing`, `backup.verify_integrity_failed` oder `backup.verify_archive_unreadable` — unabhängig davon, dass der Pfad auf der Platte existiert.

### 2. Warum wird mein Restore blockiert?

Die **Restore-Preview** analysiert die Tar-Einträge. Enthält das Archiv **absolute Pfade**, **Traversal** (`..`), **Geräte/FIFO/Hardlinks** oder andere gesperrte Mitglieder, bricht die Analyse mit **`backup.restore_blocked_entries`** ab (typische Diagnose **`RESTORE-PATH-004`**). Das schützt vor Path-Traversal und versehentlichem Schreiben außerhalb der Sandbox.

### 3. Warum kann ich nicht nach `/media` sichern?

Unter **`/media`** und **`/run/media`** gelten **Storage-Schutz**-Regeln: automatische Wechselmedien sind für produktive Schreib-Backups nicht freigegeben. Nutze dokumentierte Ziele (z. B. **`/mnt/setuphelfer/…`**). Die API meldet dann oft **`backup.path_invalid`** mit Hinweis auf **`STORAGE-PROTECTION-005`**.

### 4. Warum erkennt Setuphelfer manipulierte Backups?

**Deep-Verify** vergleicht den **extrahierten Inhalt** mit den im **MANIFEST** gespeicherten **SHA-256**-Werten. Weicht ein Byte ab (Manipulation, Bit-Rot, abgebrochener Schreibvorgang), schlägt die Prüfung mit **`backup.verify_integrity_failed`** fehl (**`BACKUP-HASH-003`**).

### 5. Was bedeutet „Integritätsprüfung fehlgeschlagen“?

Das ist die **Obermeldung** für **Deep-Verify**, wenn mindestens eine Integritätsregel verletzt ist: fehlendes/kaputtes Manifest, **Hash-Mismatch**, oder **Archiv gzip/tar nicht lesbar**. Im UI-Detail steht der konkrete **API-Code** und ggf. **`details.diagnosis_id`**.

---

## Backup & Verify (HW1-03) — common questions (EN)

### 1. Why does verify fail even though the backup file exists?

The file may exist, but **verify** (especially **`mode=deep`**) checks more than presence: **MANIFEST.json**, per-file **SHA-256**, and **gzip/tar readability**. If the manifest is missing, hashes do not match, or the archive is damaged, the API returns e.g. **`backup.failed_manifest_missing`**, **`backup.verify_integrity_failed`**, or **`backup.verify_archive_unreadable`** — even though the path exists on disk.

### 2. Why is my restore blocked?

**Restore preview** inspects tar members. If the archive contains **absolute paths**, **traversal** (`..`), **device/FIFO/hardlink** entries, or other blocked members, analysis fails with **`backup.restore_blocked_entries`** (typical diagnosis **`RESTORE-PATH-004`**). This prevents path traversal and unsafe extraction.

### 3. Why can’t I back up to `/media`?

**`/media`** and **`/run/media`** are covered by **storage protection**: auto-mounted removable paths are not allowlisted for productive write backups. Use documented targets (e.g. **`/mnt/setuphelfer/…`**). The API often reports **`backup.path_invalid`** with **`STORAGE-PROTECTION-005`**.

### 4. Why does Setuphelfer detect tampered backups?

**Deep verify** compares **extracted content** to **SHA-256** values stored in the **MANIFEST**. Any byte difference (tampering, bit rot, interrupted write) fails verification with **`backup.verify_integrity_failed`** (**`BACKUP-HASH-003`**).

### 5. What does “integrity check failed” mean?

It is the **high-level message** for **deep verify** when an integrity rule fails: missing/broken manifest, **hash mismatch**, or **unreadable gzip/tar**. The UI detail shows the concrete **API code** and optionally **`details.diagnosis_id`**.

### 6. Warum sehe ich den Preview-Ordner unter `/tmp` nicht?

Wenn `setuphelfer-backend` mit **`PrivateTmp=true`** läuft, liegt der von der API gemeldete `preview_dir` im **eigenen `/tmp`-Namespace des Dienstes**. Im normalen Host-`/tmp` ist dieser Pfad dann ggf. nicht sichtbar.  
Das ist **kein Bug**, sondern gewollte Service-Isolation. Die API liefert dazu im Preview-Response zusätzliche Felder wie `private_tmp_isolation` und `preview_dir_visibility_note`.

### 6. Why can’t I see the preview directory under `/tmp`?

When `setuphelfer-backend` runs with **`PrivateTmp=true`**, the API `preview_dir` points to the service’s **private `/tmp` namespace**. It may not be visible in the normal host `/tmp`.  
This is **not a bug**; it is expected service isolation. The preview response includes fields like `private_tmp_isolation` and `preview_dir_visibility_note`.

### 7. Warum wird bei `mode=restore` jetzt ein `target_dir` verlangt?

Seit FIX-12 ist der API-Vertrag strikt getrennt:  
- `mode=preview` analysiert nur (sichere Sandbox),  
- `mode=restore` schreibt wirklich Dateien und benötigt deshalb ein validiertes `target_dir`.  
Ohne `target_dir` liefert die API `backup.restore_target_missing`.

### 8. Warum wird mein Restore-Ziel blockiert?

Bei `mode=restore` greift dieselbe harte Zielvalidierung wie bei sicheren Schreibpfaden:  
- `/media`/`/run/media` oder andere unzulässige Ziele -> `backup.restore_target_invalid` (typisch `STORAGE-PROTECTION-*`)  
- nicht beschreibbare Ziele -> `backup.restore_not_writable` (typisch `PERM-GROUP-008`)  
- `target_dir="/"` wird immer blockiert.

### 7. Why is `target_dir` now required for `mode=restore`?

Since FIX-12, the API contract is strict:  
- `mode=preview` only analyzes in sandbox,  
- `mode=restore` performs real writes and therefore requires a validated `target_dir`.  
Missing `target_dir` returns `backup.restore_target_missing`.

### 8. Why is my restore target blocked?

In `mode=restore`, strict write-target validation is enforced:  
- `/media`/`/run/media` or other invalid targets -> `backup.restore_target_invalid` (typically `STORAGE-PROTECTION-*`)  
- non-writable target -> `backup.restore_not_writable` (typically `PERM-GROUP-008`)  
- `target_dir="/"` is always blocked.

### 9. Warum wird mein Restore nicht ausgeführt?

Häufige Ursachen sind:
- `mode=restore` ohne `target_dir` (`backup.restore_target_missing`)
- ungültiger oder gesperrter Zielpfad (`backup.restore_target_invalid`)
- Ziel nicht beschreibbar (`backup.restore_not_writable`)

### 10. Was ist der Unterschied zwischen Preview und Restore?

- **Preview**: Analyse/Tests in Sandbox, kein produktiver Write ins Zielsystem.
- **Restore**: echter Schreibvorgang in `target_dir` mit harter Zielvalidierung.

### 11. Warum kann ich nicht nach `/` oder `/media` restoren?

Zum Schutz vor Systemzerstörung sind diese Ziele blockiert:
- `/` -> Runtime-Gate (`RESTORE-RUNTIME-006`)
- `/media`/`/run/media` -> Storage-Protection (`STORAGE-PROTECTION-005`)

### 12. Warum sehe ich meine Restore-Dateien nicht?

Typische Gründe:
- falsches `target_dir` angegeben
- nur `mode=preview` statt `mode=restore` ausgeführt
- Verwechslung mit `PrivateTmp`-Preview-Pfaden unter `/tmp`

### 9. Why is my restore not executed?

Common causes:
- `mode=restore` without `target_dir` (`backup.restore_target_missing`)
- invalid or blocked target path (`backup.restore_target_invalid`)
- target is not writable (`backup.restore_not_writable`)

### 10. What is the difference between preview and restore?

- **Preview**: analysis/testing in sandbox, no productive write.
- **Restore**: real write operation to `target_dir` with strict target validation.

### 11. Why can’t I restore to `/` or `/media`?

These targets are blocked for safety:
- `/` -> runtime safety gate (`RESTORE-RUNTIME-006`)
- `/media`/`/run/media` -> storage protection (`STORAGE-PROTECTION-005`)

### 12. Why can’t I find my restore files?

Typical reasons:
- wrong `target_dir`
- ran `mode=preview` instead of `mode=restore`
- confusion with `PrivateTmp` preview paths under `/tmp`

### 7. Warum zeigt `backup/list` manchmal `status=unknown`?

Seit FIX-11 liest `GET /api/backup/list` primär aus einem lokalen Backup-Index statt direkt vom Mount zu scannen.  
Wenn ein schneller Existenz-Check (`quick_stat`) nicht rechtzeitig antwortet, bleibt der Eintrag sichtbar und wird als `status=unknown` markiert, damit der Request nicht blockiert.

### 7. Why can `backup/list` return `status=unknown`?

Since FIX-11, `GET /api/backup/list` reads from a local backup index instead of scanning the mount path directly.  
If a quick existence check (`quick_stat`) does not return within the short timeout, the entry is kept and marked as `status=unknown` to avoid blocking the API worker.
