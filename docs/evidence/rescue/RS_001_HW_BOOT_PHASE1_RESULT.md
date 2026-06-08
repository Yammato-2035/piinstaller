# RS-001 HW-Boot Phase 1 — Ergebnis

**Datum:** 2026-06-08  
**HEAD vorher:** `669adb7`  
**HEAD nachher:** `669adb7` (keine Codeänderungen in dieser Phase)  
**Branch:** `main`

---

## Ziel der Phase

HW-UEFI-Boot-Blocker eingrenzen, Boot-Artefakt statisch prüfen, reproduzierbares ISO/Handoff vorbereiten, RS-001 für Operator-HW-Test vorbereiten — **ohne** USB-Write, Backup, Restore, Netzwerk, Provisioning.

---

## Phase 0 — Gate

| Feld | Wert |
|------|------|
| Gate-Skript | `./scripts/check-runtime-profile-deploy-gate.sh` |
| Exit | **12** |
| Grund | `project_version_mismatch:1.7.8.4!=1.7.9.0` |
| Runtime-Aktionen | **blockiert** |
| Statische Analyse | **fortgesetzt** |

Fremde uncommitted Changes: u. a. `ckb-next`, Rescue-Live-Tree, diverse Evidence — **nicht angefasst**.

---

## Was geprüft wurde

1. Vorhandene IST-Analyse und USB-Triage gelesen
2. Kanonisches ISO statisch auditiert (`file`, `sha256sum`, `xorriso`, `isoinfo`, `7z`)
3. `validate-rescue-iso-uefi-boot.sh` — Deep-Check
4. Boot-Konfigurationen aus ISO extrahiert (`grub.cfg`, `live.cfg`)
5. QEMU-Serial-Smoke (2 Versuche, ohne sudo)
6. ISO-Rebuild-Preview (`run-controlled-iso-build-with-logging.sh`)
7. FAT32-ESP-Writer Dry-Run
8. Operator-Handoff erstellt

---

## Was erfolgreich war

| Prüfung | Ergebnis |
|---------|----------|
| ISO vorhanden | **ja** — 652 MiB, SHA `c9de3751...` |
| UEFI Deep-Validator | **Exit 0** — alle Flags grün |
| El-Torito BIOS + UEFI | **ja** (plain report) |
| BOOTX64.EFI + efi.img | **ja** |
| live/vmlinuz + initrd + squashfs | **ja** |
| GRUB/ISOLINUX-Pfade konsistent | **ja** |
| Custom Boot-Menü (Start Assistant, MSI-compat) | **ja** in `live.cfg` |
| HW-Blocker eingegrenzt | **ja** — MSI + isohybrid, nicht ISO-Defekt |
| Operator-Handoff | **erstellt** |
| FAT32-ESP Dry-Run | **Exit 0** (Plan vorhanden) |

---

## Was fehlschlug / offen blieb

| Punkt | Ergebnis |
|-------|----------|
| HW-Boot RS-001 | **nicht nachgewiesen** — weiterhin Operator-Pflicht |
| ISO-Rebuild | **nicht ausgeführt** — Exit 20, sudo/Operator nötig |
| QEMU-Serial (Standard-ISO) | **0 Bytes** — erwartbar ohne `console=ttyS0` |
| Operator-Fehlermodus MSI | **unbekannt** |
| RS-1.json | **rot** — Template unverändert |

---

## RS-001 Status

| Feld | Wert |
|------|------|
| Matrix-ID | RS-001 (`docs/testing/RESCUE_STICK_TEST_MATRIX.md`) |
| Evidence | `docs/evidence/rescue-stick/RS-1.json` |
| **Ampel** | **rot** |
| **Begründung** | Kein physischer Boot-Nachweis; nur Artefakt + QEMU-Historie |

**Teilfortschritt (gelb-Indiz, nicht RS-001 grün):**

- ISO-Artefakt audit **grün**
- Ursache HW-Blocker **eingegrenzt** (FAT32-ESP empfohlen)
- Operator-Handoff **bereit**

---

## Root-Cause-Einordnung (Phase 1)

```text
ISO strukturell OK  →  USB-Readback OK (historisch)  →  MSI bootet nicht
                              ↓
              Wahrscheinlich: isohybrid ISO9660 (0x17) statt FAT-ESP (0xEF)
                              ↓
              Empfohlen: FAT32-ESP-Writer (Pfad B im Operator-Handoff)
```

**Nicht behauptet:** HW-Boot ist gelöst. Das erfordert Operator-Ergebnis.

---

## Erfolgskriterium Phase 1

| Kriterium | Erfüllt |
|-----------|---------|
| A) Geprüftes ISO + Operator-Handoff | **ja** |
| B) Blocker eindeutig eingegrenzt | **ja** |

**Phase 1:** **abgeschlossen** (Artefakt + Handoff + Einordnung). RS-001 selbst bleibt **rot** bis Operator-HW-Test.

---

## Nächster enger Schritt

**Prompt:** `RESCUE_RS001_OPERATOR_HW_BOOT_FAT32_ESP` (oder manueller Operator-Lauf nach `RS_001_HW_BOOT_OPERATOR_HANDOFF.md`)

1. Operator: FAT32-ESP-Write auf MSI-Referenz-USB (`/dev/sdb` bestätigen)
2. UEFI-Boot + Fehlermodus dokumentieren
3. Bei Erfolg: `RS-1.json` auf grün, `executed_at` setzen
4. Bei Misserfolg: Kernel/GRUB-Logs, Secure-Boot-Status, BIOS-Fallback testen

---

## Neue/geänderte Dateien (diese Phase)

- `docs/evidence/rescue/RS_001_BOOT_ARTIFACT_AUDIT.md` (neu)
- `docs/evidence/rescue/RS_001_HW_BOOT_OPERATOR_HANDOFF.md` (neu)
- `docs/evidence/rescue/RS_001_HW_BOOT_PHASE1_RESULT.md` (neu)
- `docs/evidence/rescue/rs001_phase1_qemu_serial_20260608_213211/` (neu)
- `docs/evidence/rescue/rs001_phase1_qemu_serial_retry_20260608_213514/` (neu)
- `docs/evidence/rescue/RESCUE_STICK_CAPABILITY_MATRIX.yaml` (aktualisiert)
- `docs/evidence/rescue/RESCUE_STICK_GAP_LIST.md` (aktualisiert)
- `docs/evidence/rescue/RESCUE_STICK_NEXT_PHASE_INPUT.md` (aktualisiert)

---

## Nicht ausgeführt

sudo, apt, deploy, USB-Write, dd, Backup, Restore, Netzwerk, Telemetrie-Versand, ISO-Rebuild, Commit (siehe Git-Regeln).

---

## Versionierung

Keine Code-/Build-Konfigurationsänderung → **keine Versionserhöhung**.
