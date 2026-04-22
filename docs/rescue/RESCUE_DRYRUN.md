# Rescue Restore Dry-Run (Phase 2)

## Zweck

Endpunkt `POST /api/rescue/restore-dryrun` und CLI `scripts/rescue_mode.py --restore-dryrun-backup …` führen **keinen echten Restore** aus. Es werden:

- Backup-Eignung (Manifest, Typ, Integrität),
- optionales Ziel-Blockgerät (Kapazität, SMART, Partitionstabelle, UUID-Konflikte im laufenden System),
- eine **Sandbox-Extraktion** via bestehende `verify_deep`-Logik unter `/tmp/setuphelfer-rescue-dryrun-staging/<uuid>/…`,
- Boot-Heuristik auf dem extrahierten Baum (`rescue_boot_restore_check`),

zu einem **Risiko- und Entscheidungsreport** zusammengeführt.

## Modi

| `mode` | Verhalten |
|--------|------------|
| `analyze_only` | `verify_basic`, Tar-Mitglieds-Analyse, **kein** Extract; Bootbewertung bleibt unsicher → typisch **YELLOW** mit Aktion `rescue.decision.action.run_full_dryrun_for_boot`. |
| `dryrun` | Zusätzlich `verify_deep` + `restore_files(..., dry_run=True)` im erlaubten Sandbox-Pfad; anschließend Boot-Checks. |

## Berichte

- JSON: `/tmp/setuphelfer-rescue-dryrun.json`
- Markdown: `/tmp/setuphelfer-rescue-dryrun.md`

## Was Dry-Run **nicht** garantiert

- Keine echte Hardwareabbildung, kein Bootloader-Write, kein Chroot mit Schreiben auf `/`.
- Bootfähigkeit ist **heuristisch** (Dateien + fstab vs. **live** blkid).
- Verschlüsselte `.gpg`/`.enc`-Dateien: ohne echte Entschlüsselung keine vollständige Prüfung.

## Unterschied zu Phase 3

Phase 3 darf kontrolliert auf freigegebene Ziele schreiben. Phase 2 bleibt strikt **lesend** auf produktiven Pfaden und schreibt nur in definierte `/tmp`-Sandboxes für die Simulation.
