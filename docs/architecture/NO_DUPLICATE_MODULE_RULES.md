# No Duplicate Module Rules

**Gültig ab:** 2026-05-20  
**Kontext:** Rettungsstick / BR-001-OFFLINE baut auf gemeinsamen Core-Modulen auf.

---

## Verbindliche Regeln

1. **Keine zweite Storage Discovery** — lsblk/blkid/findmnt nur über `modules/storage_detection` bzw. künftig `core/storage` (oder `safe_device`-Hilfen). Deploy-Runner: nur Handoff, kein paralleler Parser.

2. **Keine zweite Mount Safety** — Runtime-Zielprüfung: `core/safe_device.validate_write_target` / `inspect_write_target_mount`. Rescue read-only: `rescue_readonly_mount_orchestrator` → später `rescue/rescue_readonly_source` mit Core-Hilfen.

3. **Kein zweiter Backup Runner** — tar/pigz/finalize/SHA256 nur `backend/tools/backup_runner.py`. Rescue startet denselben Runner mit anderem `SOURCE_ROOT` / Profil.

4. **Keine zweite Verify Engine** — `modules/backup_verify.verify_basic` / `verify_deep` only.

5. **Keine eigene Rescue-Write-Guard-Logik** — `safety/write_guard.evaluate_write_target` auf Inspect-Daten; keine dritte Regelmenge ohne ADR.

6. **Neue Rescue-Funktionen** müssen Core importieren (`from core...` / `from modules...` kanonisch). Kopierter Code > 20 Zeilen aus Core → **verboten**.

7. **Abweichungen** nur mit ADR unter `docs/architecture/adr/ADR-NNN-*.md`.

8. **`app.py`** — keine neuen Fachlogik-Blöcke > 30 Zeilen; Service extrahieren.

9. **`deploy/runner_rescue_*`** — keine neuen `subprocess` tar/rsync/dd/mkfs/parted-Aufrufe (bestehende Sandbox-Ausnahmen dokumentiert).

10. **Live-only** (apt, package_activity, mintupdate) bleibt unter `live/` bzw. `core/package_activity` — **nicht** in Rescue importieren.

---

## Prüfung

```bash
./scripts/check-module-boundaries.sh
```

Exit **0** = keine Warnungen; Exit **1** = Warnungen (blockiert CI erst wenn explizit aktiviert).

---

## Review-Checkliste (PR)

- [ ] Importiert Rescue-Code Core statt Kopie?  
- [ ] Kein neuer lsblk/findmnt-Parser?  
- [ ] Kein zweiter backup_runner?  
- [ ] Tests für geänderte Public Functions?  
- [ ] ADR bei bewusster Abweichung?
