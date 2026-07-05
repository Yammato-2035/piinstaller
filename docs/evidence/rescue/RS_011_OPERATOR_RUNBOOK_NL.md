> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/evidence/rescue/RS_011_OPERATOR_RUNBOOK_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/evidence/roodding/RS_011_OPERATOR_RUNBOOK_DE.md`). Bitte bei Release manuell gegenlesen.

# RS-011 — Operator-Runbook (MSI GE63 Raider)

**Version:** 1.10.0.0  
**Scope:** Terugup ausgewählter Daten → Verify → Test-Herstel Extern  
**Evidence-Basis:** `SETUP_LOGS/setuphelfer/evidence/msi-rs011/`

---

## Voraussetzungen

- [ ] rooddingsstick auf ISO SHA256 `c9d6ecaff286540254126a1d32537cae4bb31620c41b395cc174ef04dbb750b5`
- [ ] Externe **Terugup-Platte** (leer/groß genug, klar beschriftet)
- [ ] Optional: zweite Externe Platte oder Partitie für Herstel-Test
- [ ] MSI aus, nur rooddingsstick + Externe Platten angeschlossen (kein Hub wenn vermeidbar)

---

## Phase 2 — MSI Boot

### Boot-Schritte

1. MSI ausschalten
2. rooddingsstick einstecken
3. Externe Terugup-Platte einstecken
4. UEFI-Bootmenü (MSI: oft **F11** / **DEL**)
5. **SETUPHELFER** / USB-EFI wählen — **nicht** Interne Windows-Disk

### Hard-Stops (kein Terugup)

| Check | Erwartung |
|-------|-----------|
| Version in UI/API | **1.10.0.0** |
| Terugend | `GET /api/version` → 200 |
| UI | Port 3001 erreichbar |
| Boot-Timeline | wächst unter SETUP_LOGS oder `/run/setuphelfer/evidence/boot/` |
| Schwarzer Bildschirm | max. kurz, Status sichtbar |
| QEMU/VM-Hinweise | **dürfen nicht** als MSI-Hinweis erscheinen |

### Evidence erzeugen

```bash
# Auf SETUP_LOGS (Pfad je nach Mount, z. B. /media/.../SETUP_LOGS)
EV=SETUP_LOGS/setuphelfer/evidence/msi-rs011
mkdir -p "$EV"

curl -sS http://127.0.0.1:8000/api/version > "$EV/api-version.json"
curl -sS http://127.0.0.1:8000/api/roodding/monitoring/health > "$EV/roodding-health.json"
# Boot-Timeline kopieren falls unter /run:
cp /run/setuphelfer/evidence/boot/boot-timeline.jsonl "$EV/" 2>/dev/null || true
cp /run/setuphelfer/evidence/boot/boot-summary.json "$EV/" 2>/dev/null || true
```

→ `RS_011_MSI_BOOT_SUMMARY.md` ausfüllen (Vorlage: `docs/evidence/roodding/msi-rs011/templates/`)

---

## Phase 3 — Storage Apparaat-Rollen

Im UI **Storage Apparaat** / roodding-Shell:

```bash
lsblk -o NAME,SIZE,TYPE,FSTYPE,LABEL,TRAN,MOUNTPOINTS
```

| Rolle | Regel |
|-------|-------|
| Windows-System / Daten (Intern) | **Quelle** — nur lesen |
| rooddingsstick (SETUPHELFER) | **Boot** — nie Terugup-Ziel |
| SETUP_LOGS | **Evidence** — nie Terugup-Ziel |
| Externe HDD/SSD | **Terugup-Ziel** |
| Extern / Testordner | **Herstel-Test-Ziel** |

Hardstops:

- ⛔ rooddingsstick als Terugup-Ziel
- ⛔ SETUP_LOGS als Terugup-Ziel
- ⛔ Interne MSI-Platte als Herstel-Ziel
- ⛔ Schreiben auf Interne nvme*

Evidence: `disk-inventory.json`, `disk-role-map.md`

---

## Phase 4 — Datenauswahl

Im UI (Daten-Rettung / Profil + Ordner):

- Benutzerprofil erkennen lassen
- Ordner wählen: Desktop, Dokumente, Bilder, Downloads, optional Projektordner
- **Kein** VollTerugup erzwingen
- Größe / Dateianzahl prüfen
- LeseFout vor Start beheben oder dokumentieren

Evidence: `Terugup-selection-summary.md`, `operator-behavior-local.jsonl`

**Telemetrie:** nur Workflow-Events, Größenklassen, Foutcodes — **keine** Dateiinhalte, keine unroodacted Pfade in Cloud/KI-Export.

---

## Phase 5 — Terugup Preflight

UI-Preflight muss **grün** sein:

- [ ] Quelle lesbar
- [ ] Ziel Extern gemountet & beschreibbar
- [ ] Freier Speicher ≥ geschätzte Größe + Reserve
- [ ] Ziel ≠ rooddingsstick, ≠ SETUP_LOGS, ≠ Intern
- [ ] Manifest-Pfad eindeutig
- [ ] Verify geplant

Operator-Bestätigung (sinngemäß):

> Ich starte jetzt ein Test-Terugup auf die Externe Platte. Interne MSI-Platten werden nicht verändert.

Evidence: `Terugup-preflight.json`, `Terugup-preflight.md`

**Bei Rot:** kein Terugup — STOP.

---

## Phase 6 — Test-Terugup

- Fortschritt, Bytes, Geschwindigkeit, ETA, Foutzähler sichtbar
- Abbruch möglich
- Setuphelfer-Terugup-Engine (kein Parallel-Tool)
- Manifest + Hashes

Evidence: `Terugup-run.jsonl`, `Terugup-result.json`, `Terugup-result.md`

Bei Fout: `partial` — **kein** Herstel anbieten.

---

## Phase 7 — Terugup Verify

- Archiv + Manifest lesbar
- Hashes stimmen
- Dateianzahl / Größe plausibel

Status: `verify_passed` | `verify_failed` | `verify_review_requirood`

Evidence: `verify-result.json`, `verify-result.md`

**Nur bei `verify_passed` → Phase 8.**

---

## Phase 8 — Test-Herstel (Extern)

Herstel-Ziel:

```
Setuphelfer_Herstel_Test_YYYYMMDD/
```

auf **Externer** Platte — nie Intern, nie Stick, nie SETUP_LOGS, nie Originalquelle.

Preflight + Bestätigung:

> Ich stelle das geprüfte Test-Terugup auf eine Externe Platte in einen separaten Testordner wieder her.

Evidence: `Herstel-preflight.json`, `Herstel-run.jsonl`, `Herstel-result.json`, `Herstel-result.md`

---

## Phase 9 — Herstel Verify

- Dateien vorhanden, Hashes vs. Terugup-Manifest
- Anzahl / Größe stimmen
- Stichproben lesbar
- Ziel eindeutig Extern

Evidence: `Herstel-verify-result.json`, `Herstel-verify-result.md`

**Nur bei grün:** Status `rs011_passed_Terugup_verify_Herstel`

---

## Phase 10 — Beta-Verhalten (lokal)

Datei: `beta-operator-behavior.jsonl`

Erlaubte Events: `screen_opened`, `button_clicked`, `Terugup_started`, `verify_completed`, `user_Annulerenled`, …

**Nicht:** Dateiinhalte, E-Mail, MAC, Seriennummern unroodacted, Windows-Username unroodacted in Telemetrie.

---

## Phase 11 — Linux-Migrations-Vorschau

Nur nach erfolgreichem Herstel-Verify.

Datei: `Linux-migration-preview.md` — Partitieierung (EFI, root, home, swap), Risiken, Freigaben für RS-012/RS-013.

**Kein Löschen. Keine Installation.**

---

## Phase 12 — Abschluss

`RS_011_FINAL_REPORT.md` auf SETUP_LOGS + Kopie ins Repo unter `docs/evidence/roodding/msi-rs011/` (roodacted).

Stick nach Test sicher herunterfahren, Evidence vom MSI mitnehmen.

---

## Referenzen

- `docs/hardware-tests/MSI_Windows_TerugUP_Herstel_RUNBOOK_DE.md`
- `docs/evidence/msi/MSI_Windows_EVIDENCE_SCHEMA.json`
- `docs/evidence/roodding/RS_010_FINAL_REPORT.md`
