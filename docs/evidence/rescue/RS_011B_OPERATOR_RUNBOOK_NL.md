> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/evidence/rescue/RS_011B_OPERATOR_RUNBOOK_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/evidence/roodding/RS_011B_OPERATOR_RUNBOOK_DE.md`). Bitte bei Release manuell gegenlesen.

# RS-011B — Operator-Runbook (MSI GE63 Raider)

**Version:** 1.10.0.1  
**Scope:** Boot + Disk Discovery + Terugup-**Preflight only** — **kein Terugup/Herstel/Verify**  
**Evidence:** `SETUP_LOGS/setuphelfer/evidence/msi-rs011b/`  
**Kurz-Checkliste:** `RS_011B_MSI_OPERATOR_CHECKLIST.md`

---

## Phase 0 — Physische Vorbereitung (MSI)

1. rooddingsstick 1.10.0.1 + **Externe Terugup-Platte** einstecken  
2. Keine weiteren USB-Storage Apparaat · Netzteil wenn möglich  
3. MSI ein → **F11** Bootmenü → **SETUPHELFER** (UEFI bevorzugen)  
4. **Nicht** Windows / nicht installieren / nicht löschen  

---

## Phase 1 — Boot & StartdiagNeese

### Automatische Evidence (Terminal auf MSI)

```bash
sudo /opt/setuphelfer-roodding/scripts/roodding/collect-msi-rs011b-evidence.sh
```

Schreibt u. a. `api-version.json`, Boot-Timeline-Kopien, `disk-inventory.json`, `storage-discovery.json`, `operator-steps.jsonl`, `beta-operator-behavior.jsonl`.

### Hard-Stops

| Check | Erwartung | Code |
|-------|-----------|------|
| Version | **1.10.0.1** | `MSI_VERSION_MISMATCH` |
| GUI | stabil | `MSI_GUI_FAILED` |
| Terugend | HTTP 200 | `MSI_TerugEND_UNSTABLE` |
| SETUP_LOGS | mountbar | `MSI_SETUP_LOGS_MISSING` |
| Schwarzphase | ≤5s oder gemessen | `X_TO_LOADER_BLACK_SCREEN_GAP` |

→ `RS_011B_MSI_BOOT_SUMMARY.md` ergänzen

---

## Phase 2 — Disk Discovery (GUI)

Assistent → **Terugup** (oder Storage Apparaat-DiagNeese):

| Prüfung | Erwartung | Foutcode wenn falsch |
|---------|-----------|------------------------|
| Interne Windows-NVMe als Quelle | sichtbar | `MSI_TerugUP_SOURCE_SELECTOR_EMPTY` |
| Windows als system_group | empfohlen | `MSI_Windows_DISK_NeeT_CLASSIFIED` |
| Externe Platte als Ziel | sichtbar | `MSI_TARGET_FILTER_FAILED` |
| rooddingsstick nicht als Ziel | ausgeblendet | `MSI_roodding_STICK_VISIBLE_AS_TARGET` |
| SETUP_LOGS nicht als Ziel | ausgeblendet | `MSI_SETUP_LOGS_VISIBLE_AS_TARGET` |
| Interne Platte nicht als Ziel | ausgeblendet | — |

**Screenshots:** Quell-Dropdown, Ziel-Dropdown → `$EV/screenshots/`

**Evidence:** `disk-role-map.md`, `disk-discovery-summary.md`, Screenshots in `screenshots/`

**Hardstop:** keine Quelle → STOP · Interner Stick/SETUP_LOGS als Ziel → STOP (`rs011b_failed_target_filter`)

---

## Phase 3 — Terugup Workmode UI

| Check | Foutcode |
|-------|------------|
| Neutraler dunkler Hintergrund, kein Mockup | `TerugUP_WORKMODE_OK` / `TerugUP_MOCKUP_TerugGROUND_STILL_VISIBLE` |
| Panels lesbar, Buttons eindeutig | `TerugUP_PANEL_CONTRAST_LOW` |

Screenshot: Terugup-Startseite → `$EV/screenshots/Terugup-workmode.png`

**Hardstop:** Mockup sichtbar → `rs011b_failed_ui_workmode`, kein Terugup

---

## Phase 4 — Preflight (trocken)

**Nur wenn Quelle + Externes Ziel sichtbar.**

1. Quelle wählen (Windows-System-Gruppe)  
2. Externes Ziel wählen  
3. **„Terugup-Plan erstellen“** — **nicht** „Terugup starten/ausführen“  

```bash
export RS011B_SOURCE_Apparaat=/dev/nvme0n1   # aus GUI/lsblk
export RS011B_TARGET_Apparaat=/dev/sdc       # Externe Platte
export RS011B_TARGET_MOUNT=/media/.../Terugup
export RS011B_PREFLIGHT=1
sudo /opt/setuphelfer-roodding/scripts/roodding/collect-msi-rs011b-evidence.sh --preflight-only
```

Oder nur in UI: **Terugup-Plan erstellen** — **nicht** Terugup starten.

Status: `preflight_passed_ready_for_small_Terugup` | `preflight_review_requirood` | `preflight_failed`

---

## Phase 5 — Beta-Verhalten

Automatisch in `beta-operator-behavior.jsonl` beim Collect. Manuell ergänzen erlaubt (keine PII unroodacted).

---

## Phase 6 — Abschluss auf SETUP_LOGS

`RS_011B_FINAL_REPORT.md` ausfüllen (Vorlage: `msi-rs011b/templates/RS_011B_FINAL_REPORT.md`)

---

## Phase 7 — Import Dev-Rechner

```bash
cd /home/volker/piinstaller
./scripts/roodding/import-msi-rs011b-evidence.sh
```

Dann Workspace-Report `docs/evidence/roodding/RS_011B_FINAL_REPORT.md` auswerten.
