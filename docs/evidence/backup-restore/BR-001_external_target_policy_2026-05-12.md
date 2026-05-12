# BR-001 — Externe Backup-Zielstrategie (Policy, STRICT)

**Datum:** 2026-05-12  
**Modus:** Dokumentation und Evidence — **kein** Backup, **kein** Restore, **kein** Formatieren, **keine** automatischen Mount-/ACL-Änderungen.

## Verbindlicher strategischer Pfad (Doku)

**`/media/setuphelfer/setuphelfer-back`**

- Nur verwendbar, wenn der Pfad **auf einem externen Blockgerät** liegt (Mount-Quelle **nicht** Root-/System-NVMe).
- **Nicht** anlegen auf dem Root-Dateisystem „unter `/media`“ ohne externes Medium.
- Wenn Medium bereits unter anderem Mountpunkt hängt (z. B. **`/media/gabriel/setuphelfer-back`**): **keine** automatische Umdeutigung — Betreiberentscheidung (Mount/Bind/Freigabe).

## Priorität externer Medien

1. Externe NVMe  
2. Externe SSD  
3. Externe HDD  
4. USB-Stick  
5. SD-Karte  

Interne Systemlaufwerke, Boot/EFI, typische Windows-Systempartitionen: **nicht** als Ziel.

## Safety

- Kein stiller Ausweichpfad nach `/tmp`, `/home`, `/var`, `/`.
- Kein Backup-Start ohne erfolgreichen **target-check**.
- Ohne Traversierung/Schreibrecht: Freigabe einholen (Diagnose **STORAGE-PROTECTION-006** nach Backend-Aktualisierung).

## Verweise

- `docs/backup/BACKUP_TARGET_POLICY_DE.md` / `BACKUP_TARGET_POLICY_EN.md`
- `docs/knowledge-base/backup/BACKUP_TARGET_SELECTION.md`
- `docs/evidence/backup-restore/BR-001_external_target_selection_2026-05-12.md`
