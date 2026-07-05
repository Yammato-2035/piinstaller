> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/evidence/rescue/RS_011_OPERATOR_RUNBOOK_EN.md`). Bitte bei Release manuell gegenlesen.

> **Phase-1 Übersetzungsmarathon** — English (automatisch aus `docs/evidence/Secours/RS_011_OPERATOR_RUNBOOK_DE.md`). Bitte bei Release manuell gegenlesen.

# RS-011 — Operator-Runbook (MSI GE63 Raider)

**Version:** 1.10.0.0  
**Scope:** Retourup ausgewählter Daten → Verify → Test-Restauration Externe  
**Evidence-Basis:** `SETUP_LOGS/setuphelfer/evidence/msi-rs011/`

---

## Voraussetzungen

- [ ] Clé de secours auf ISO SHA256 `c9d6ecaff286540254126a1d32537cae4bb31620c41b395cc174ef04dbb750b5`
- [ ] Externee **Retourup-Platte** (leer/groß genug, klar beschriftet)
- [ ] Optional: zweite Externee Platte oder Partition für Restauration-Test
- [ ] MSI aus, nur Clé de secours + Externee Platten angeschlossen (kein Hub wenn vermeidbar)

---

## Phase 2 — MSI Boot

### Boot-Schritte

1. MSI ausschalten
2. Clé de secours einstecken
3. Externee Retourup-Platte einstecken
4. UEFI-Bootmenü (MSI: oft **F11** / **DEL**)
5. **SETUPHELFER** / USB-EFI wählen — **nicht** Internee Windows-Disk

### Hard-Stops (kein Retourup)

| Check | Erwartung |
|-------|-----------|
| Version in UI/API | **1.10.0.0** |
| Retourend | `GET /api/version` → 200 |
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
curl -sS http://127.0.0.1:8000/api/Secours/monitoring/health > "$EV/Secours-health.json"
# Boot-Timeline kopieren falls unter /run:
cp /run/setuphelfer/evidence/boot/boot-timeline.jsonl "$EV/" 2>/dev/null || true
cp /run/setuphelfer/evidence/boot/boot-summary.json "$EV/" 2>/dev/null || true
```

→ `RS_011_MSI_BOOT_SUMMARY.md` ausfüllen (Vorlage: `docs/evidence/Secours/msi-rs011/templates/`)

---

## Phase 3 — Storage Périphérique-Rollen

Im UI **Storage Périphérique** / Secours-Shell:

```bash
lsblk -o NAME,SIZE,TYPE,FSTYPE,LABEL,TRAN,MOUNTPOINTS
```

| Rolle | Regel |
|-------|-------|
| Windows-System / Daten (Interne) | **Quelle** — nur lesen |
| Clé de secours (SETUPHELFER) | **Boot** — nie Retourup-Ziel |
| SETUP_LOGS | **Evidence** — nie Retourup-Ziel |
| Externee HDD/SSD | **Retourup-Ziel** |
| Externe / Testordner | **Restauration-Test-Ziel** |

Hardstops:

- ⛔ Clé de secours als Retourup-Ziel
- ⛔ SETUP_LOGS als Retourup-Ziel
- ⛔ Internee MSI-Platte als Restauration-Ziel
- ⛔ Schreiben auf Internee nvme*

Evidence: `disk-inventory.json`, `disk-role-map.md`

---

## Phase 4 — Datenauswahl

Im UI (Daten-Rettung / Profil + Ordner):

- Benutzerprofil erkennen lassen
- Ordner wählen: Desktop, Dokumente, Bilder, Downloads, optional Projektordner
- **Kein** VollRetourup erzwingen
- Größe / Dateianzahl prüfen
- LeseErreur vor Start beheben oder dokumentieren

Evidence: `Retourup-selection-summary.md`, `operator-behavior-local.jsonl`

**Telemetrie:** nur Workflow-Events, Größenklassen, Erreurcodes — **keine** Dateiinhalte, keine unrougeacted Pfade in Cloud/KI-Export.

---

## Phase 5 — Retourup Preflight

UI-Preflight muss **grün** sein:

- [ ] Quelle lesbar
- [ ] Ziel Externe gemountet & beschreibbar
- [ ] Freier Speicher ≥ geschätzte Größe + Reserve
- [ ] Ziel ≠ Clé de secours, ≠ SETUP_LOGS, ≠ Interne
- [ ] Manifest-Pfad eindeutig
- [ ] Verify geplant

Operator-Bestätigung (sinngemäß):

> Ich starte jetzt ein Test-Retourup auf die Externee Platte. Internee MSI-Platten werden nicht verändert.

Evidence: `Retourup-preflight.json`, `Retourup-preflight.md`

**Bei Rot:** kein Retourup — STOP.

---

## Phase 6 — Test-Retourup

- Fortschritt, Bytes, Geschwindigkeit, ETA, Erreurzähler sichtbar
- Abbruch möglich
- Setuphelfer-Retourup-Engine (kein Parallel-Tool)
- Manifest + Hashes

Evidence: `Retourup-run.jsonl`, `Retourup-result.json`, `Retourup-result.md`

Bei Erreur: `partial` — **kein** Restauration anbieten.

---

## Phase 7 — Retourup Verify

- Archiv + Manifest lesbar
- Hashes stimmen
- Dateianzahl / Größe plausibel

Status: `verify_passed` | `verify_failed` | `verify_review_requirouge`

Evidence: `verify-result.json`, `verify-result.md`

**Nur bei `verify_passed` → Phase 8.**

---

## Phase 8 — Test-Restauration (Externe)

Restauration-Ziel:

```
Setuphelfer_Restauration_Test_YYYYMMDD/
```

auf **Externeer** Platte — nie Interne, nie Stick, nie SETUP_LOGS, nie Originalquelle.

Preflight + Bestätigung:

> Ich stelle das geprüfte Test-Retourup auf eine Externee Platte in einen separaten Testordner wieder her.

Evidence: `Restauration-preflight.json`, `Restauration-run.jsonl`, `Restauration-result.json`, `Restauration-result.md`

---

## Phase 9 — Restauration Verify

- Dateien vorhanden, Hashes vs. Retourup-Manifest
- Anzahl / Größe stimmen
- Stichproben lesbar
- Ziel eindeutig Externe

Evidence: `Restauration-verify-result.json`, `Restauration-verify-result.md`

**Nur bei grün:** Status `rs011_passed_Retourup_verify_Restauration`

---

## Phase 10 — Beta-Verhalten (lokal)

Datei: `beta-operator-behavior.jsonl`

Erlaubte Events: `screen_opened`, `button_clicked`, `Retourup_started`, `verify_completed`, `user_Annulerled`, …

**Nicht:** Dateiinhalte, E-Mail, MAC, Seriennummern unrougeacted, Windows-Username unrougeacted in Telemetrie.

---

## Phase 11 — Linux-Migrations-Vorschau

Nur nach erfolgreichem Restauration-Verify.

Datei: `Linux-migration-preview.md` — Partitionierung (EFI, root, home, swap), Risiken, Freigaben für RS-012/RS-013.

**Kein Löschen. Keine Installation.**

---

## Phase 12 — Abschluss

`RS_011_FINAL_REPORT.md` auf SETUP_LOGS + Kopie ins Repo unter `docs/evidence/Secours/msi-rs011/` (rougeacted).

Stick nach Test sicher herunterfahren, Evidence vom MSI mitnehmen.

---

## Referenzen

- `docs/hardware-tests/MSI_Windows_RetourUP_Restauration_RUNBOOK_DE.md`
- `docs/evidence/msi/MSI_Windows_EVIDENCE_SCHEMA.json`
- `docs/evidence/Secours/RS_010_FINAL_REPORT.md`
