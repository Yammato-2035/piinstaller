# Partitionshelfer 1.7.13.1 – Post-Validation Cleanup

**Datum:** 2026-06-10  
**HEAD vorher:** `9ef5690` (nur Evidence)  
**HEAD nach Fix-Commit:** `72173b2`  
**HEAD nach Modal-Fix:** `a0a9469`  
**Runtime (API):** `1.7.13.1` (Deploy 1.7.13.2 ausstehend – Operator sudo)

## Commit-Status

| Commit | Hash | Inhalt |
|--------|------|--------|
| Fix-Code 1.7.13.1 | `72173b2` | `storage_role_classification_v2`, Tests, `partitionRoleUtils`, Version 1.7.13.1 |
| Modal-Defer | `a0a9469` | `App.tsx`, `SudoPasswordDialog.tsx`, Version 1.7.13.2 |

**Antwort:** Der eigentliche 1.7.13.1-Fix war **nicht** committed (nur Evidence `9ef5690`). Jetzt **vollständig** in `72173b2`.

### Gezielt gestagte Fix-Dateien (72173b2)

| Datei | Änderung | 1.7.13.1? |
|-------|----------|-----------|
| `backend/core/storage_role_classification.py` | USB-Backup-Erkennung v2 | **JA** |
| `backend/tests/test_storage_role_classification_windows_v1.py` | Backup-HDD-Test | **JA** |
| `frontend/src/lib/partition/partitionRoleUtils.ts` | Kein „Linux erkannt“ bei backup_target | **JA** |
| `config/version.json` + abgeleitete Versionen | 1.7.13.1 | **JA** |

## Modal-Ursache & Anpassung

| Aspekt | Detail |
|--------|--------|
| **Komponenten** | `FirstRunWizard` (Schritt 1 „Systemcheck“), `SudoPasswordDialog` (global in `App.tsx`) |
| **Trigger** | `!firstRunDone` → Vollbild-Wizard; API `/api/users/sudo-password/check` → `need_password` → Sudo-Overlay |
| **Route** | `?page=partitions` lud Seite, Overlays blieben global sichtbar (z-50) |

### Lösung (a0a9469, keine Partitionshelfer-/Klassifikations-Änderung)

1. `isPartitionsDeepLink()` → `firstRunDone` initial true bei `?page=partitions`
2. `FirstRunWizard` nur wenn `currentPage !== 'partitions'`
3. `SudoPasswordDialog deferAutoPrompt={currentPage === 'partitions'}` → kein Auto-Overlay; Systemcheck bleibt über Dashboard/Wizard erreichbar

## Deploy & Gates

| Schritt | Ergebnis |
|---------|----------|
| `sudo ./scripts/deploy-to-opt.sh` | **Blockiert** (sudo-Passwort in dieser Session nicht verfügbar) |
| Profile Gate | Exit 12 — Workspace `1.7.13.2` ≠ Runtime `1.7.13.1` |
| Backend Version Gate | Exit 14 — gleicher Drift |
| Storage-Rollen API (Runtime 1.7.13.1) | **Unverändert korrekt** (siehe Tabelle) |

**Operator-Aktion:** Deploy `a0a9469` nach `/opt`, dann Gates erneut.

## Storage-Rollen (Regression, Runtime API)

| Gerät | Rolle | Confidence | write_allowed |
|-------|-------|------------|---------------|
| `/dev/sda` | **backup_target** | high | false |
| `/dev/nvme1n1` | windows_system_disk | high | false |
| `/dev/nvme0n1` | linux_system_disk | high | false |
| `/dev/sdb` | rescue_stick | high | false |

Hardstop `/dev/sda`: `backup_target`, kein `target_is_linux_system_disk`.

## UI-Sichtprüfung & Screenshot

| Kriterium | Ergebnis |
|-----------|----------|
| Kein Sudo-Modal bei `?page=partitions` | **JA** (Build 1.7.13.2, vite preview :5174) |
| Kein Systemcheck-Overlay | **JA** |
| Partitionshelfer-Shell sichtbar | **JA** |
| Read-only Badge | **JA** |
| Sicherheitsstatus-Panel | **JA** |
| Restore-Handoff-Kachel | **JA** |

**Screenshot:** `docs/evidence/ui/PARTITIONSHELFER_1_7_13_1_CLEAN_SCREENSHOT.png`  
**Hinweis:** Headless-Capture gegen vite preview; API-Banner kann kurz erscheinen (Chrome-Timing). Produktiv unter `:3001` nach Deploy erwartet volle Datenträgerkarten.

## Verbleibende Mängel

- Deploy 1.7.13.2 auf `/opt` durch Operator (sudo)
- Gates erst nach Deploy grün
- Headless-Screenshot ohne Live-Datenträgerkarten (Timing/Preview); API bestätigt Rollen separat

## Constraints eingehalten

- Kein Partition-Write, Queue Apply, Restore Execute
- Keine Klassifikations-/Hardstop-Änderung in Cleanup
- Kein `git add -A`
