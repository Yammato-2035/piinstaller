# Rescue USB Payload Update Contract

**Feature:** PI-RS-USB-UPDATER-001  
**Operation:** `atomic_fat32_esp_payload_replace`

## Kanonische Wahrheit

Die **einzige autoritative Versionsquelle** vor dem USB-Schreiben ist der zu kopierende SquashFS-Payload.

Pflicht-Lesepfade im Payload (via `unsquashfs -cat`):

| Pfad | Feld | Erwartung |
|------|------|-----------|
| `VERSION` | Zeileninhalt | z. B. `1.10.0.16` |
| `config/rescue_payload_version.json` | `rescue_payload_version` | identisch |
| `config/version.json` | `project_version` | identisch |

Der Dateiname `filesystem.squashfs.repacked-<version>` ist ein **zusätzlicher Hinweis**, keine alleinige Wahrheitsquelle.

## Source-Preflight (vor jedem USB-Write)

1. Payload vorhanden, reguläre Datei, kein Symlink
2. SHA256 stimmt (wenn `--expected-sha256` gesetzt)
3. SquashFS read-only inspizierbar
4. Alle internen Versionsträger vorhanden und identisch
5. Version entspricht `--expected-version` (wenn gesetzt)
6. Content-Gate und Secret-Gate grün (vor physischem Write)

### Stop-Bedingungen

| Bedingung | Code |
|-----------|------|
| Interne Träger weichen ab | `source_payload_version_drift` |
| Dateiname vs. interne Version | `source_payload_filename_version_mismatch` |
| SHA256 falsch | `source_payload_hash_mismatch` |

## Ziel-Preflight

- USB-Transport, Modell/Kapazität plausibel (Intenso Ultra Line ~59G)
- Partition Label `SETUPHELFER`, VFAT
- Schwesterpartition `SETUP_LOGS` auf demselben Gerät
- Keine interne Systemplatte, kein Mount auf `/`
- Partition **nicht gemountet** (Updater mountet selbst)
- Freier Speicher ausreichend

## Atomare Reihenfolge

```
source verify → target verify → snapshot
→ payload to .sqtmp/filesystem.squashfs.new
→ temp payload sync + SHA256 verify
→ temp metadata erzeugen + validate
→ .prev backup (falls fehlend)
→ atomic payload activate (mv)
→ atomic metadata activate (cp)
→ filesystem sync
→ final payload + metadata verify
→ success evidence
```

## ESP-Metadaten (kanonisches Schema)

Mindestfelder in `setuphelfer/rescue/version.json`:

```json
{
  "project_version": "1.10.0.16",
  "rescue_payload_version": "1.10.0.16",
  "payload_filename": "live/filesystem.squashfs",
  "payload_sha256": "cada647ccc11a545a8b4eb6f42deb8745bdedcd5b1662e738c96d68c987621b5",
  "updated_at": "<ISO8601 UTC>",
  "update_method": "atomic_fat32_esp_payload_replace",
  "content_verified": true
}
```

**Nicht zulässig:**

- `project_version` aus altem Stick übernehmen
- Version nur aus Dateiname ableiten
- Fehlende Felder manuell nachtragen nach erfolgreichem Lauf

Zusätzliche Felder aus bestehendem `version.json` (z. B. `git_commit`, `built_at`) dürfen erhalten bleiben, Versionsfelder werden überschrieben.

## Rollback

| Phase | Verhalten |
|-------|-----------|
| Fehler vor Payload-Aktivierung | Alter Payload unverändert; Temp-Dateien entfernen |
| Fehler nach Payload-, vor Metadaten-Aktivierung | Payload aus `.prev-*` wiederherstellen; Metadaten unverändert |
| Rollback fehlgeschlagen | `critical_manual_recovery_required` |

## `.prev-*`-Policy

- Pro Update maximal eine neue `.prev-<old_version>`-Datei
- Version aus ESP-Metadaten des alten aktiven Payloads
- Historische `.prev-*` nicht blind löschen
- Keine unkontrollierte Kette neuer Prev-Dateien

## Unverändert lassen

- Partitionstabelle
- `SETUP_LOGS`-Partition (kein Schreibzugriff)
- Interne Datenträger

## Maschinenlesbares Ergebnis

Updater schreibt strukturiertes JSON (`build_usb_updater_result`) mit Status:
`success | blocked | failed | failed_rolled_back | critical_manual_recovery_required`
