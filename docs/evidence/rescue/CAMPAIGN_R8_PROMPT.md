# CAMPAIGN R.8 — Rebuild + USB + MSI Boot Marker Validation

**Voraussetzung:** R.6 committed (`feat(rescue): add early boot evidence persistence hook`), Version **1.7.18.0**.

## Ziel

Nachweis auf echter Hardware, dass der R.6 Boot-Persistence-Hook im **neuen ISO** aktiv ist und nach MSI-Boot erzeugt:

```
/setuphelfer-evidence/boot/boot_marker.md
/setuphelfer-evidence/boot/boot_marker.json
```

## Nicht-Ziele

- Keine neuen Features
- Keine UI-Änderungen
- Kein Deploy
- Kein Backup/Restore
- Keine Partition-Writes auf interne Datenträger

## Sicherheitsregeln

- **USB-Write nur** mit `OPERATOR_USB_WRITE_FREIGABE=1`
- **ISO-Build nur** mit `--operator-confirm-build` im Operator-TTY
- Kein `git add -A`
- Evidence **redacted** (keine Seriennummern, MACs, Hardware-IDs)
- Nur freigegebener Rettungsstick

---

## Phase 1 — Gate-Status

```bash
git rev-parse --short HEAD
python3 -c "import json; print(json.load(open('config/version.json'))['project_version'])"
./scripts/check-runtime-deploy-gate.sh || true
```

Evidence: `docs/evidence/rescue/R8_PHASE0_STATUS.md`

---

## Phase 2 — R.6 im HEAD prüfen

| Check | Erwartung |
|-------|-----------|
| `setuphelfer-rescue-boot-evidence-init` in HEAD | FOUND |
| `initialize_boot_evidence_marker` in `rescue_persistence.py` | FOUND |
| `RESCUE_PERSISTENCE_VERSION = 4` | FOUND |
| `build_r6_boot_persistence_matrix_entries` | FOUND |
| `test_rescue_boot_persistence_hook_r6.py` | FOUND |

Evidence: `docs/evidence/rescue/R8_R6_HEAD_VALIDATION.md`

---

## Phase 3 — Temp-Runtime Bundle

```bash
./scripts/rescue-live/create-temp-runtime-bundle.sh
```

Evidence: `docs/evidence/rescue/R8_TEMP_RUNTIME_BUNDLE.md`

---

## Phase 4 — Prepare

```bash
./scripts/rescue-live/prepare-controlled-live-build-tree.sh --profile standard
```

Evidence: `docs/evidence/rescue/R8_PREPARE_RESULT.md`

---

## Phase 5 — Validate Tree

```bash
./scripts/rescue-live/validate-controlled-live-build-tree.sh
```

Exit **0** erforderlich.

Evidence: `docs/evidence/rescue/R8_VALIDATE_TREE.md`

---

## Phase 6 — ISO Build (Operator)

```bash
sudo ./scripts/rescue-live/run-controlled-iso-build-with-logging.sh \
  --operator-confirm-build --profile standard --run-id r8_$(date +%Y%m%d_%H%M%S)
```

Erfassen: ISO-Pfad, Größe, SHA256, `LB_EXIT`.

Evidence: `docs/evidence/rescue/R8_CONTROLLED_BUILD.md`

---

## Phase 7 — SquashFS Validation

Pflicht **FOUND**:

| Artefakt |
|----------|
| `setuphelfer-rescue-boot-evidence-init` |
| `rescue_persistence.py` v4 + `initialize_boot_evidence_marker` |
| `setuphelfer-rescue-evidence.py` mit `boot-init` |
| `start-assistant` mit boot-hook |
| `rescue_test_matrix.py` R6-Einträge |

Entscheidung: `ready_for_usb_write` oder `blocked_runtime`

Evidence: `docs/evidence/rescue/R8_SQUASHFS_VALIDATION.md`

---

## Phase 8 — USB Write (Operator)

Nur bei `OPERATOR_USB_WRITE_FREIGABE=1`:

```bash
export OPERATOR_USB_WRITE_FREIGABE=1
# USB_TARGET setzen, Operator-Gates
./scripts/rescue-live/write-fat32-esp-rescue-usb.sh --execute-write ...
```

Evidence: `docs/evidence/rescue/R8_USB_WRITE.md`

---

## Phase 9 — Verify FAT32 ESP

```bash
./scripts/rescue-live/verify-fat32-esp-rescue-usb.sh
```

Evidence: `docs/evidence/rescue/R8_USB_VERIFY.md`

---

## Phase 10 — MSI Hardware Boot (Operator)

Beobachtungen **ohne Interpretation**:

- GRUB sichtbar?
- Setuphelfer Branding?
- Linux startet?
- TUI / Kiosk / React UI?
- WLAN, Eingabegeräte?
- Fehlermeldungen?

Evidence: `docs/evidence/rescue/R8_OPERATOR_BOOT_OBSERVATION.md`

---

## Phase 11 — Stick Runtime Evidence Review

Nach Rückkehr des Sticks:

```bash
find /media/*/SETUPHELFER/setuphelfer-evidence -type f
```

Inventar: `boot/`, `matrix/`, `hardware/`, `telemetry/`, `menu/`

Evidence: `docs/evidence/rescue/R8_RUNTIME_EVIDENCE_REVIEW.md`

---

## Phase 12 — Boot Marker Validation

| Datei | Kriterium |
|-------|-----------|
| `setuphelfer-evidence/boot/boot_marker.md` | **muss existieren** |
| `setuphelfer-evidence/boot/boot_marker.json` | **muss existieren** |

Bewertung: `R8_BOOT_MARKER_OK` oder `R8_BOOT_MARKER_MISSING`

Evidence: `docs/evidence/rescue/R8_BOOT_MARKER_VALIDATION.md`

---

## Phase 13 — RS-001 Status

| Ampel | Kriterium |
|-------|-----------|
| **red** | Kein Hardware-Nachweis |
| **yellow** | Linux ok, Persistence teilweise |
| **green** | Hardware-Boot + Evidence auf Stick |

Evidence: `docs/evidence/rescue/R8_RS001_STATUS.md`

---

## Phase 14 — Abschluss

`docs/evidence/rescue/R8_FINAL_RESULT.md`

Enthält: HEAD, Version, ISO SHA256, USB Verify, MSI-Ergebnis, Boot-Marker, RS-001, nächster Schritt.

---

## Erfolgskriterium R.8

**R8_BOOT_MARKER_OK** auf dem Stick nach MSI-Boot mit neuem 1.7.18.0-Image.
