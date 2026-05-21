# Rettungsstick — Core-Abhängigkeiten (BR-001-OFFLINE)

**Stand:** 2026-05-20  
**Gate:** BR-001-OFFLINE ist Release-Gate; Live-BR-001 ist experimentell.

---

## Muss Core nutzen (nicht duplizieren)

| Schritt | Core-/Kanon-Modul | Heute |
|--------|-------------------|--------|
| Storage Discovery | **`core.storage_facade`**, `modules/storage_detection`, `core/safe_device` | Deploy-Runner nur Handoff; **kein** eigener lsblk-Parser |
| Mount / RO-Plan | **`core.mount_facade`**, `runner_rescue_readonly_mount_orchestrator` | Plan only — kein mount subprocess im MVP |
| Zielprüfung extern | `safe_device.validate_write_target`, `backup_target_service_access` | API `target-check` in `app.py` |
| Write Guard (Preview) | `safety/write_guard.evaluate_write_target` | `rescue/orchestrator.py` |
| Backup Profile offline-full | `core/backup_profiles`, `core/backup_archive_options` | Profil `full-root-stable` als Vorlage → **`offline-full`** |
| Backup Runner | `tools/backup_runner.py` | systemd `setuphelfer-backup@` |
| Manifest + SHA256 | Runner finalize + `modules/backup_engine` | — |
| Verify Deep | `modules/backup_verify.verify_deep` | Runner-Hook |
| Evidence | `tools/backup_evidence_collector`, release-gates JSON | RS-008 |
| Restore Preview | `modules/rescue_restore_dryrun`, `rescue/orchestrator` preview | kein Execute |
| Notifications | `core/notification_service` | optional Failure/Success |

---

## Rescue-spezifisch (neu/erweitern, Orchestration only)

| Modul (Soll) | Zweck |
|--------------|--------|
| `rescue/rescue_boot_context.py` | `mode=rescue`, Pfade, keine Live-apt |
| `rescue/rescue_storage_orchestrator.py` | interne + externe Medien listen |
| `rescue/rescue_readonly_source.py` | Quellplatte RO mounten |
| `rescue/rescue_backup_orchestrator.py` | Offline-Job starten (Env, sudo-Gate) |
| `rescue/rescue_restore_preview.py` | UI/API für Preview |

**Deploy-Runner** bleiben für Lab/Handoff; Produktlogik wandert nicht in Runner.

---

## Darf nicht dupliziert werden

- lsblk/findmnt/blkid-Parser  
- tar/pigz-Kommandozeilen (außer `backup_runner`)  
- SHA256-Berechnung  
- verify_deep Implementierung  
- STORAGE-PROTECTION / SYSTEM-DISK-Heuristiken  
- E-Mail-SMTP-Versand

---

## Offline-BR-001 Ablauf (Soll)

```mermaid
sequenceDiagram
  participant Boot as Rescue Boot
  participant Ctx as rescue_boot_context
  participant Stor as core.storage
  participant RO as rescue_readonly_source
  participant Safe as core.safety
  participant Run as backup_runner
  participant Ver as backup_verify
  participant Ev as core.evidence

  Boot->>Ctx: mode=rescue
  Ctx->>Stor: discover internal + external
  Stor->>RO: mount source read-only
  RO->>Safe: validate external target writable
  Safe->>Run: offline-full profile, SOURCE_ROOT mounted
  Run->>Run: tar/pigz, finalize, SHA256
  Run->>Ver: verify_deep
  Run->>Ev: job + RS evidence
```

1. Bootstick erkennt `rescue`.  
2. Storage Discovery: interne Quelle + externes Ziel.  
3. Quelle read-only mounten.  
4. Ziel write-guard / target-check.  
5. Offline backup via **ein** Runner + Profil `offline-full`.  
6. Manifest + SHA256.  
7. Verify Deep.  
8. Evidence (RS-006/007, BR-001-OFFLINE JSON).  
9. Restore Preview **separat** (kein Execute im MVP).

---

## Fehlende MVP-Bausteine (kein Core-Duplikat nötig)

- Materialisierte Debian-Live-Config / ISO-Build-Abnahme  
- Offline-UI im Live-System  
- HW-E2E RS-001–RS-008  
- Partitionierungsassistent (Restore Ersatzplatte — **später**, nicht Backup-Blocker)  
- Malware-Scan optional vor Restore (UI-Warnung, kein Backup-Blocker)

---

## Abnahme

Rettungsstick-Implementierung **freigegeben** nach Monolith-Audit, wenn jeder neue PR `NO_DUPLICATE_MODULE_RULES` und `check-module-boundaries.sh` einhält.
