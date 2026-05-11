# Restore-Risiko- und Entscheidungsmodell (Phase 2)

## Felder in der API-Antwort

| Feld | Bedeutung |
|------|-----------|
| `restore_risk_level` | `green` \| `yellow` \| `red` — aggregierte Ampel aus `findings`. |
| `restore_decision` | Maschinenlesbare Handlungsempfehlung (siehe unten). |
| `findings` | Liste aus `RescueFinding`: `code`, `area`, `risk_level`, `evidence` (keine UI-Freitexte). |
| `recommended_actions` | Stabile Aktions-Codes (i18n unter `rescue.decision.action.*`). |

## `restore_decision` Werte

| Wert | Bedingung (vereinfacht) |
|------|-------------------------|
| `proceed_possible` | `BACKUP_OK`, `DRYRUN_OK`, `BOOTABLE_LIKELY`, keine roten Blocker. |
| `proceed_with_explicit_risk_ack` | Technisch möglich, aber unsichere Bootlage, SMART-Warnungen, `analyze_only`, oder Schlüssel-„vorhanden“ ohne echte Entschlüsselung. |
| `do_not_restore` | Inkrementell ohne Vollbackup, Dry-Run blockiert, verschlüsselt ohne Schlüssel-Flag, harte Archiv-Blocker. |
| `recommend_new_target_disk` | Kapazität unzureichend oder SMART kritisch (Zielbewertung). |
| `recommend_data_recovery_first` | Backup wirkt **korrupt** (`BACKUP_CORRUPT` / Verify-Fail). |

## Ampel-Regeln (Prinzip)

- **RED** schlägt vor **GREEN** (konservativ).
- Ohne `dryrun`-Extract keine **grüne** Boot-Zusage — `analyze_only` max. **YELLOW** mit Hinweis auf vollen Dry-Run.
- Kein „grün“, wenn `findings` einen roten Code enthalten (Aggregation überschreibt).

## Grenzen

- SMART und blkid können Root-Rechte erfordern — fehlende Daten führen zu **YELLOW**, nicht zu „grün durch Ignorieren“.
- `fstab`-UUID-Check vergleicht mit **aktueller** blkid-Umgebung, nicht mit Zielhardware nach Restore.
