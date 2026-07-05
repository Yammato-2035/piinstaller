# RS-011B — Operator-Runbook (MSI GE63 Raider)

**Version:** 1.10.0.1  
**Scope:** Boot + Disk Discovery + Backup-**Preflight only** — **kein Backup/Restore/Verify**  
**Evidence:** `SETUP_LOGS/setuphelfer/evidence/msi-rs011b/`  
**Kurz-Checkliste:** `RS_011B_MSI_OPERATOR_CHECKLIST.md`

---

## Phase 0 — Physische Vorbereitung (MSI)

1. Rettungsstick 1.10.0.1 + **externe Backup-Platte** einstecken  
2. Keine weiteren USB-Datenträger · Netzteil wenn möglich  
3. MSI ein → **F11** Bootmenü → **SETUPHELFER** (UEFI bevorzugen)  
4. **Nicht** Windows / nicht installieren / nicht löschen  

---

## Phase 1 — Boot & Startdiagnose

### Automatische Evidence (Terminal auf MSI)

```bash
sudo /opt/setuphelfer-rescue/scripts/rescue/collect-msi-rs011b-evidence.sh
```

Schreibt u. a. `api-version.json`, Boot-Timeline-Kopien, `disk-inventory.json`, `storage-discovery.json`, `operator-steps.jsonl`, `beta-operator-behavior.jsonl`.

### Hard-Stops

| Check | Erwartung | Code |
|-------|-----------|------|
| Version | **1.10.0.1** | `MSI_VERSION_MISMATCH` |
| GUI | stabil | `MSI_GUI_FAILED` |
| Backend | HTTP 200 | `MSI_BACKEND_UNSTABLE` |
| SETUP_LOGS | mountbar | `MSI_SETUP_LOGS_MISSING` |
| Schwarzphase | ≤5s oder gemessen | `X_TO_LOADER_BLACK_SCREEN_GAP` |

→ `RS_011B_MSI_BOOT_SUMMARY.md` ergänzen

---

## Phase 2 — Disk Discovery (GUI)

Assistent → **Backup** (oder Datenträger-Diagnose):

| Prüfung | Erwartung | Fehlercode wenn falsch |
|---------|-----------|------------------------|
| Interne Windows-NVMe als Quelle | sichtbar | `MSI_BACKUP_SOURCE_SELECTOR_EMPTY` |
| Windows als system_group | empfohlen | `MSI_WINDOWS_DISK_NOT_CLASSIFIED` |
| Externe Platte als Ziel | sichtbar | `MSI_TARGET_FILTER_FAILED` |
| Rettungsstick nicht als Ziel | ausgeblendet | `MSI_RESCUE_STICK_VISIBLE_AS_TARGET` |
| SETUP_LOGS nicht als Ziel | ausgeblendet | `MSI_SETUP_LOGS_VISIBLE_AS_TARGET` |
| Interne Platte nicht als Ziel | ausgeblendet | — |

**Screenshots:** Quell-Dropdown, Ziel-Dropdown → `$EV/screenshots/`

**Evidence:** `disk-role-map.md`, `disk-discovery-summary.md`, Screenshots in `screenshots/`

**Hardstop:** keine Quelle → STOP · interner Stick/SETUP_LOGS als Ziel → STOP (`rs011b_failed_target_filter`)

---

## Phase 3 — Backup Workmode UI

| Check | Fehlercode |
|-------|------------|
| Neutraler dunkler Hintergrund, kein Mockup | `BACKUP_WORKMODE_OK` / `BACKUP_MOCKUP_BACKGROUND_STILL_VISIBLE` |
| Panels lesbar, Buttons eindeutig | `BACKUP_PANEL_CONTRAST_LOW` |

Screenshot: Backup-Startseite → `$EV/screenshots/backup-workmode.png`

**Hardstop:** Mockup sichtbar → `rs011b_failed_ui_workmode`, kein Backup

---

## Phase 4 — Preflight (trocken)

**Nur wenn Quelle + externes Ziel sichtbar.**

1. Quelle wählen (Windows-System-Gruppe)  
2. Externes Ziel wählen  
3. **„Backup-Plan erstellen“** — **nicht** „Backup starten/ausführen“  

```bash
export RS011B_SOURCE_DEVICE=/dev/nvme0n1   # aus GUI/lsblk
export RS011B_TARGET_DEVICE=/dev/sdc       # externe Platte
export RS011B_TARGET_MOUNT=/media/.../Backup
export RS011B_PREFLIGHT=1
sudo /opt/setuphelfer-rescue/scripts/rescue/collect-msi-rs011b-evidence.sh --preflight-only
```

Oder nur in UI: **Backup-Plan erstellen** — **nicht** Backup starten.

Status: `preflight_passed_ready_for_small_backup` | `preflight_review_required` | `preflight_failed`

---

## Phase 5 — Beta-Verhalten

Automatisch in `beta-operator-behavior.jsonl` beim Collect. Manuell ergänzen erlaubt (keine PII unredacted).

---

## Phase 6 — Abschluss auf SETUP_LOGS

`RS_011B_FINAL_REPORT.md` ausfüllen (Vorlage: `msi-rs011b/templates/RS_011B_FINAL_REPORT.md`)

---

## Phase 7 — Import Dev-Rechner

```bash
cd /home/volker/piinstaller
./scripts/rescue/import-msi-rs011b-evidence.sh
```

Dann Workspace-Report `docs/evidence/rescue/RS_011B_FINAL_REPORT.md` auswerten.
