# RS-001 HW-Boot Phase 2 — FAT32-ESP Operator-Vorbereitung

**Datum:** 2026-06-08  
**HEAD vorher:** `2fa3ea3`  
**HEAD nachher:** `2fa3ea3` (keine Codeänderung; nur Evidence-Vorbereitung)  
**Branch:** `main`  
**Modus:** Operator-Handoff — Cursor führt **keine** destruktiven Schritte aus

---

## Phase 0 — Gate

| Feld | Wert |
|------|------|
| Gate-Skript | `./scripts/check-runtime-deploy-gate.sh` |
| Exit | **0** (Legacy-Hinweis: dev-dashboard 404 im Release-Profil — für Operator-Boot **kein Stopper**) |
| Dirty Tree | Ja — viele fremde uncommitted Changes; **nicht angefasst** |
| Laufart | Ausschließlich Operator-/Evidence-Vorbereitung |

---

## Phase 1 — Handoff-Validierung

| Prüfung | Ergebnis |
|---------|----------|
| Handoff vorhanden | **ja** — `RS_001_HW_BOOT_OPERATOR_HANDOFF.md` |
| ISO-Pfad vorhanden | **ja** |
| SHA256 identisch | **ja** — `c9de3751f7fafe51c836d112bac99331c06252a01430b41f2a50b432ca63f194` |
| FAT32-ESP als Pfad B dokumentiert | **ja** |
| dd/isohybrid nicht primär | **ja** — Pfad A nur Fallback; **Pfad B empfohlen** |
| MSI-Triage enthalten | **ja** |
| Readback-/Verify-Schritte | **ja** (Pfad A); FAT32-Verify via blkid/ESP-Checks (Pfad B) |

**operator_handoff_invalid:** **nein** — Handoff gültig, Operator-Lauf empfohlen.

---

## Phase 2–4 — Operator-Aktionen (vom Nutzer auszuführen)

Cursor hat **nicht** ausgeführt: `sudo`, `dd`, `parted`, `mkfs`, `wipefs`, Mount auf USB, HW-Boot.

### Schritt 1 — Geräteprüfung (Operator)

```bash
# Vor USB:
lsblk -o NAME,PATH,SIZE,MODEL,TRAN,TYPE,FSTYPE,MOUNTPOINTS

# USB einstecken, 5s warten:
lsblk -o NAME,PATH,SIZE,MODEL,TRAN,TYPE,FSTYPE,MOUNTPOINTS

# Zurückmelden:
# USB_DEVICE=  USB_SIZE=  USB_MODEL=  CONFIRMED_NOT_INTERNAL=yes
```

### Schritt 2 — ISO prüfen

```bash
cd /home/volker/piinstaller
export ISO_PATH="build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso"
export EXPECTED_SHA256="c9de3751f7fafe51c836d112bac99331c06252a01430b41f2a50b432ca63f194"
sha256sum "$ISO_PATH"
# Abweichung → STOP
```

### Schritt 3 — FAT32-ESP (empfohlen: Repo-Skript)

**Variante Repo (bevorzugt):**

```bash
cd /home/volker/piinstaller
export USB_DEVICE="<BEWUSST_ERSETZEN>"   # z. B. /dev/sdb

# Dry-run:
./scripts/rescue-live/write-fat32-esp-rescue-usb.sh \
  --iso build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso \
  --target "$USB_DEVICE" \
  --dry-run

# Write-Vorbereitung (gibt write_manual aus — Operator führt Schritte im Terminal aus):
./scripts/rescue-live/write-fat32-esp-rescue-usb.sh \
  --iso build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso \
  --target "$USB_DEVICE" \
  --operator-confirm-write \
  --confirm-phrase "WRITE SETUPHELFER FAT32 ESP USB"
```

Das Skript führt **keinen** automatischen Write aus; es druckt die Operator-Befehle (`sgdisk`, `mkfs.vfat`, `rsync`, …).

**Variante manuell (Fallback):** siehe User-Prompt Phase 3.3–3.7 (parted GPT + mkfs.vfat + ISO-Extraktion per `7z` oder loop-mount + rsync).

### Schritt 4 — ESP-Inhalt prüfen (nach Write, Operator)

```bash
# Auf gemountetem ESP oder per Stick-Readonly-Mount:
test -f .../EFI/BOOT/BOOTX64.EFI && echo BOOTX64_OK
test -f .../boot/grub/grub.cfg && echo GRUB_CFG_OK
test -f .../live/vmlinuz && echo VMLINUX_OK
test -f .../live/initrd.img && echo INITRD_OK
test -f .../live/filesystem.squashfs && echo SQUASHFS_OK
```

### Schritt 5 — HW-Boot MSI (Operator)

Firmware: Secure Boot **off**, UEFI **on**, Fast Boot **off**.

| Test | Dokumentieren |
|------|---------------|
| A — UEFI Boot | Stick im Menü? GRUB? Kernel? Live? Setuphelfer-TUI? |
| B — MSI-Kompatibilitätsmodus | `nomodeset`-Eintrag |
| C — Legacy/CSM | nur falls UEFI scheitert |

Ergebnis in `RS_001_HW_BOOT_OPERATOR_RESULT_TEMPLATE.md` ausfüllen → als `RS_001_HW_BOOT_OPERATOR_RESULT.md` speichern.

---

## Phase 5–6 — Auswertung

| Feld | Status |
|------|--------|
| Operator-Ergebnis eingegangen | **nein** |
| `RS_001_HW_BOOT_OPERATOR_RESULT.md` | **nicht erstellt** (kein Fake-Green) |
| ESP-Inhalt geprüft (HW) | **nein** |
| UEFI-HW-Boot | **nicht belegt** |
| MSI-Kompatibilitätsmodus | **nicht belegt** |
| Legacy-Test | **nicht belegt** |

### RS-001 Status

| ID | Ampel | Begründung |
|----|-------|------------|
| RS-001 | **rot** | Kein physischer Boot-Nachweis; Operator-Lauf ausstehend |
| `docs/evidence/rescue-stick/RS-1.json` | **rot** (Template) | `executed_at: null` |

**Nicht gesetzt:** grün/gelb — keine Operator-Rückmeldung.

---

## Erfolgskriterium dieser Phase

| Kriterium | Erfüllt |
|-----------|---------|
| Handoff validiert | **ja** |
| Operator-Template bereit | **ja** |
| Operator-Anleitung konsolidiert | **ja** |
| HW-Boot nachgewiesen | **nein** — erfordert Operator |

**Phase 2:** **teilweise abgeschlossen** (Vorbereitung); **blockiert** auf Operator-HW-Test.

---

## Nächster Schritt

1. Operator führt FAT32-ESP-Write + HW-Boot auf MSI durch
2. Füllt `RS_001_HW_BOOT_OPERATOR_RESULT_TEMPLATE.md` aus
3. Cursor/Nächster Prompt wertet `RS_001_HW_BOOT_OPERATOR_RESULT.md` aus und aktualisiert RS-1.json + Capability Matrix

**Nächster enger Prompt:** `RESCUE_RS001_OPERATOR_RESULT_INGEST` (nach Operator-Rückmeldung)

---

## Neue Dateien (diese Phase)

- `docs/evidence/rescue/RS_001_HW_BOOT_OPERATOR_RESULT_TEMPLATE.md`
- `docs/evidence/rescue/RS_001_HW_BOOT_PHASE2_RESULT.md`

---

*Nicht ausgeführt: sudo, dd, USB-Write, HW-Boot, ISO-Rebuild, Deploy.*
