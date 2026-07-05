# RS-011 — Operator-Runbook (MSI GE63 Raider)

**Version:** 1.10.0.0  
**Scope:** Backup ausgewählter Daten → Verify → Test-Restore extern  
**Evidence-Basis:** `SETUP_LOGS/setuphelfer/evidence/msi-rs011/`

---

## Voraussetzungen

- [ ] Rettungsstick auf ISO SHA256 `c9d6ecaff286540254126a1d32537cae4bb31620c41b395cc174ef04dbb750b5`
- [ ] Externe **Backup-Platte** (leer/groß genug, klar beschriftet)
- [ ] Optional: zweite externe Platte oder Partition für Restore-Test
- [ ] MSI aus, nur Rettungsstick + externe Platten angeschlossen (kein Hub wenn vermeidbar)

---

## Phase 2 — MSI Boot

### Boot-Schritte

1. MSI ausschalten
2. Rettungsstick einstecken
3. Externe Backup-Platte einstecken
4. UEFI-Bootmenü (MSI: oft **F11** / **DEL**)
5. **SETUPHELFER** / USB-EFI wählen — **nicht** interne Windows-Disk

### Hard-Stops (kein Backup)

| Check | Erwartung |
|-------|-----------|
| Version in UI/API | **1.10.0.0** |
| Backend | `GET /api/version` → 200 |
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
curl -sS http://127.0.0.1:8000/api/rescue/monitoring/health > "$EV/rescue-health.json"
# Boot-Timeline kopieren falls unter /run:
cp /run/setuphelfer/evidence/boot/boot-timeline.jsonl "$EV/" 2>/dev/null || true
cp /run/setuphelfer/evidence/boot/boot-summary.json "$EV/" 2>/dev/null || true
```

→ `RS_011_MSI_BOOT_SUMMARY.md` ausfüllen (Vorlage: `docs/evidence/rescue/msi-rs011/templates/`)

---

## Phase 3 — Datenträger-Rollen

Im UI **Datenträger** / Rescue-Shell:

```bash
lsblk -o NAME,SIZE,TYPE,FSTYPE,LABEL,TRAN,MOUNTPOINTS
```

| Rolle | Regel |
|-------|-------|
| Windows-System / Daten (intern) | **Quelle** — nur lesen |
| Rettungsstick (SETUPHELFER) | **Boot** — nie Backup-Ziel |
| SETUP_LOGS | **Evidence** — nie Backup-Ziel |
| Externe HDD/SSD | **Backup-Ziel** |
| Extern / Testordner | **Restore-Test-Ziel** |

Hardstops:

- ⛔ Rettungsstick als Backup-Ziel
- ⛔ SETUP_LOGS als Backup-Ziel
- ⛔ Interne MSI-Platte als Restore-Ziel
- ⛔ Schreiben auf interne nvme*

Evidence: `disk-inventory.json`, `disk-role-map.md`

---

## Phase 4 — Datenauswahl

Im UI (Daten-Rettung / Profil + Ordner):

- Benutzerprofil erkennen lassen
- Ordner wählen: Desktop, Dokumente, Bilder, Downloads, optional Projektordner
- **Kein** Vollbackup erzwingen
- Größe / Dateianzahl prüfen
- Lesefehler vor Start beheben oder dokumentieren

Evidence: `backup-selection-summary.md`, `operator-behavior-local.jsonl`

**Telemetrie:** nur Workflow-Events, Größenklassen, Fehlercodes — **keine** Dateiinhalte, keine unredacted Pfade in Cloud/KI-Export.

---

## Phase 5 — Backup Preflight

UI-Preflight muss **grün** sein:

- [ ] Quelle lesbar
- [ ] Ziel extern gemountet & beschreibbar
- [ ] Freier Speicher ≥ geschätzte Größe + Reserve
- [ ] Ziel ≠ Rettungsstick, ≠ SETUP_LOGS, ≠ intern
- [ ] Manifest-Pfad eindeutig
- [ ] Verify geplant

Operator-Bestätigung (sinngemäß):

> Ich starte jetzt ein Test-Backup auf die externe Platte. Interne MSI-Platten werden nicht verändert.

Evidence: `backup-preflight.json`, `backup-preflight.md`

**Bei Rot:** kein Backup — STOP.

---

## Phase 6 — Test-Backup

- Fortschritt, Bytes, Geschwindigkeit, ETA, Fehlerzähler sichtbar
- Abbruch möglich
- Setuphelfer-Backup-Engine (kein Parallel-Tool)
- Manifest + Hashes

Evidence: `backup-run.jsonl`, `backup-result.json`, `backup-result.md`

Bei Fehler: `partial` — **kein** Restore anbieten.

---

## Phase 7 — Backup Verify

- Archiv + Manifest lesbar
- Hashes stimmen
- Dateianzahl / Größe plausibel

Status: `verify_passed` | `verify_failed` | `verify_review_required`

Evidence: `verify-result.json`, `verify-result.md`

**Nur bei `verify_passed` → Phase 8.**

---

## Phase 8 — Test-Restore (extern)

Restore-Ziel:

```
Setuphelfer_Restore_Test_YYYYMMDD/
```

auf **externer** Platte — nie intern, nie Stick, nie SETUP_LOGS, nie Originalquelle.

Preflight + Bestätigung:

> Ich stelle das geprüfte Test-Backup auf eine externe Platte in einen separaten Testordner wieder her.

Evidence: `restore-preflight.json`, `restore-run.jsonl`, `restore-result.json`, `restore-result.md`

---

## Phase 9 — Restore Verify

- Dateien vorhanden, Hashes vs. Backup-Manifest
- Anzahl / Größe stimmen
- Stichproben lesbar
- Ziel eindeutig extern

Evidence: `restore-verify-result.json`, `restore-verify-result.md`

**Nur bei grün:** Status `rs011_passed_backup_verify_restore`

---

## Phase 10 — Beta-Verhalten (lokal)

Datei: `beta-operator-behavior.jsonl`

Erlaubte Events: `screen_opened`, `button_clicked`, `backup_started`, `verify_completed`, `user_cancelled`, …

**Nicht:** Dateiinhalte, E-Mail, MAC, Seriennummern unredacted, Windows-Username unredacted in Telemetrie.

---

## Phase 11 — Linux-Migrations-Vorschau

Nur nach erfolgreichem Restore-Verify.

Datei: `linux-migration-preview.md` — Partitionierung (EFI, root, home, swap), Risiken, Freigaben für RS-012/RS-013.

**Kein Löschen. Keine Installation.**

---

## Phase 12 — Abschluss

`RS_011_FINAL_REPORT.md` auf SETUP_LOGS + Kopie ins Repo unter `docs/evidence/rescue/msi-rs011/` (redacted).

Stick nach Test sicher herunterfahren, Evidence vom MSI mitnehmen.

---

## Referenzen

- `docs/hardware-tests/MSI_WINDOWS_BACKUP_RESTORE_RUNBOOK_DE.md`
- `docs/evidence/msi/MSI_WINDOWS_EVIDENCE_SCHEMA.json`
- `docs/evidence/rescue/RS_010_FINAL_REPORT.md`
