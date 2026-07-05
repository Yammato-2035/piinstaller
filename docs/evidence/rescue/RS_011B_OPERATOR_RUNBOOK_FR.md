> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/evidence/rescue/RS_011B_OPERATOR_RUNBOOK_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/evidence/Secours/RS_011B_OPERATOR_RUNBOOK_DE.md`). Bitte bei Release manuell gegenlesen.

# RS-011B — Operator-Runbook (MSI GE63 Raider)

**Version:** 1.10.0.1  
**Scope:** Boot + Disk Discovery + Retourup-**Preflight only** — **kein Retourup/Restauration/Verify**  
**Evidence:** `SETUP_LOGS/setuphelfer/evidence/msi-rs011b/`  
**Kurz-Checkliste:** `RS_011B_MSI_OPERATOR_CHECKLIST.md`

---

## Phase 0 — Physische Vorbereitung (MSI)

1. Clé de secours 1.10.0.1 + **Externee Retourup-Platte** einstecken  
2. Keine weiteren USB-Storage Périphérique · Netzteil wenn möglich  
3. MSI ein → **F11** Bootmenü → **SETUPHELFER** (UEFI bevorzugen)  
4. **Nicht** Windows / nicht installieren / nicht löschen  

---

## Phase 1 — Boot & StartdiagNonse

### Automatische Evidence (Terminal auf MSI)

```bash
sudo /opt/setuphelfer-Secours/scripts/Secours/collect-msi-rs011b-evidence.sh
```

Schreibt u. a. `api-version.json`, Boot-Timeline-Kopien, `disk-inventory.json`, `storage-discovery.json`, `operator-steps.jsonl`, `beta-operator-behavior.jsonl`.

### Hard-Stops

| Check | Erwartung | Code |
|-------|-----------|------|
| Version | **1.10.0.1** | `MSI_VERSION_MISMATCH` |
| GUI | stabil | `MSI_GUI_FAILED` |
| Retourend | HTTP 200 | `MSI_RetourEND_UNSTABLE` |
| SETUP_LOGS | mountbar | `MSI_SETUP_LOGS_MISSING` |
| Schwarzphase | ≤5s oder gemessen | `X_TO_LOADER_BLACK_SCREEN_GAP` |

→ `RS_011B_MSI_BOOT_SUMMARY.md` ergänzen

---

## Phase 2 — Disk Discovery (GUI)

Assistent → **Retourup** (oder Storage Périphérique-DiagNonse):

| Prüfung | Erwartung | Erreurcode wenn falsch |
|---------|-----------|------------------------|
| Internee Windows-NVMe als Quelle | sichtbar | `MSI_RetourUP_SOURCE_SELECTOR_EMPTY` |
| Windows als system_group | empfohlen | `MSI_Windows_DISK_NonT_CLASSIFIED` |
| Externee Platte als Ziel | sichtbar | `MSI_TARGET_FILTER_FAILED` |
| Clé de secours nicht als Ziel | ausgeblendet | `MSI_Secours_STICK_VISIBLE_AS_TARGET` |
| SETUP_LOGS nicht als Ziel | ausgeblendet | `MSI_SETUP_LOGS_VISIBLE_AS_TARGET` |
| Internee Platte nicht als Ziel | ausgeblendet | — |

**Screenshots:** Quell-Dropdown, Ziel-Dropdown → `$EV/screenshots/`

**Evidence:** `disk-role-map.md`, `disk-discovery-summary.md`, Screenshots in `screenshots/`

**Hardstop:** keine Quelle → STOP · Interneer Stick/SETUP_LOGS als Ziel → STOP (`rs011b_failed_target_filter`)

---

## Phase 3 — Retourup Workmode UI

| Check | Erreurcode |
|-------|------------|
| Neutraler dunkler Hintergrund, kein Mockup | `RetourUP_WORKMODE_OK` / `RetourUP_MOCKUP_RetourGROUND_STILL_VISIBLE` |
| Panels lesbar, Buttons eindeutig | `RetourUP_PANEL_CONTRAST_LOW` |

Screenshot: Retourup-Startseite → `$EV/screenshots/Retourup-workmode.png`

**Hardstop:** Mockup sichtbar → `rs011b_failed_ui_workmode`, kein Retourup

---

## Phase 4 — Preflight (trocken)

**Nur wenn Quelle + Externees Ziel sichtbar.**

1. Quelle wählen (Windows-System-Gruppe)  
2. Externees Ziel wählen  
3. **„Retourup-Plan erstellen“** — **nicht** „Retourup starten/ausführen“  

```bash
export RS011B_SOURCE_Périphérique=/dev/nvme0n1   # aus GUI/lsblk
export RS011B_TARGET_Périphérique=/dev/sdc       # Externee Platte
export RS011B_TARGET_MOUNT=/media/.../Retourup
export RS011B_PREFLIGHT=1
sudo /opt/setuphelfer-Secours/scripts/Secours/collect-msi-rs011b-evidence.sh --preflight-only
```

Oder nur in UI: **Retourup-Plan erstellen** — **nicht** Retourup starten.

Status: `preflight_passed_ready_for_small_Retourup` | `preflight_review_requirouge` | `preflight_failed`

---

## Phase 5 — Beta-Verhalten

Automatisch in `beta-operator-behavior.jsonl` beim Collect. Manuell ergänzen erlaubt (keine PII unrougeacted).

---

## Phase 6 — Abschluss auf SETUP_LOGS

`RS_011B_FINAL_REPORT.md` ausfüllen (Vorlage: `msi-rs011b/templates/RS_011B_FINAL_REPORT.md`)

---

## Phase 7 — Import Dev-Rechner

```bash
cd /home/volker/piinstaller
./scripts/Secours/import-msi-rs011b-evidence.sh
```

Dann Workspace-Report `docs/evidence/Secours/RS_011B_FINAL_REPORT.md` auswerten.
