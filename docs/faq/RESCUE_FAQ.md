# FAQ – Rescue / Bootstick (Phase 0–3)

## Was ist der Rescue-Stick?

Ein geplantes **minimales Bootsystem** mit Setuphelfer-**Read-only-Diagnose** (siehe `docs/architecture/RESCUE_BOOT_ARCHITECTURE.md`). Phase 0/1 liefern Konzept + Analyse; **Phase 2** ergänzt **Restore-Dry-Run** ohne echtes Überschreiben; **Phase 3** erlaubt einen **kontrollierten echten Restore** nur mit Dry-Run-Token, Bestätigungen und erlaubten Zielpfaden.

## Macht die Diagnose Änderungen an meiner Platte?

**Nein** — bewusst keine Schreibzugriffe auf erkannte Systemlaufwerke, kein Restore, kein automatisches Schreib-Mount. `fsck` und `xfs_repair` laufen nur mit **`-n`** und nur, wenn das Ziel **nicht** gemountet ist.

## Was macht der Restore-Dry-Run?

- Prüft Backup-Pfade (Allowlist), Archiv-Inhalt (Symlink-/Pfadregeln wie bei Restore/Verify), optional Zielplatte.
- Schreibt **nur** in Sandbox unter `/tmp/setuphelfer-rescue-dryrun-staging/…` für `verify_deep`.
- **Kein** `dd`, **kein** Bootloader-Write, **kein** Root-Overwrite.

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
