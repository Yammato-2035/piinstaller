# Kampagne R.5 — Controlled ISO Build + Stick Write + MSI Boot Test

**Voraussetzung:** R.4 committed (`feat(rescue): prepare browser kiosk and boot verification`, Version `1.7.17.0`)

---

## Ziel

Rettungsstick mit Browser/Kiosk/GRUB-Staging auf MSI-Rechner booten und alle Evidence unter `/setuphelfer-evidence/` verifizieren.

**ISO-Build und USB-Write nur mit expliziter Operator-Freigabe.**

---

## Harte Sicherheitsregeln

| Verboten | Erlaubt |
|----------|---------|
| Backup-Execute / Restore | Read-only MSI-Diagnose |
| Partition-Write / Format intern | Evidence auf erkanntem Rettungsstick |
| rw-Mount interne NVMe/HDD/SSD | Controlled ISO Build (isoliert) |
| Deploy ohne Gate | USB-Write nach Operator-Freigabe |
| apt install auf Host | — |

**Interne Datenträger:** read-only — Matrix `R3-INTERNAL-001` muss `green` bleiben.

**Bei Bootfehler:** Fotos/Notizen zusätzlich in Evidence (`summaries/`, `raw/`) dokumentieren.

---

## Phase 1 — Gate-Status

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
./scripts/check-runtime-deploy-gate.sh || true
./scripts/check-module-boundaries.sh || true
```

Evidence: `docs/evidence/rescue/R5_PHASE0_STATUS.md`

---

## Phase 2 — Build-Konfiguration prüfen

Prüfen vor Build:

- `setuphelfer.list.chroot` — chromium, xserver-xorg, openbox, …
- `includes.chroot/etc/xdg/openbox/autostart`
- `prepare-controlled-live-build-tree.sh` — kiosk/evidence/ui-launch in sbin-Liste
- Workspace-Version = `1.7.17.0`

Evidence: `docs/evidence/rescue/R5_BUILD_CONFIG_VERIFY.md`

---

## Phase 3 — Grafische Assets stagen

```bash
./scripts/rescue-live/stage-rescue-graphical-assets.sh
```

Prüfen: `build/rescue/asset-manifest.json`, GRUB-Theme unter `includes.binary/boot/grub/themes/setuphelfer/`

Evidence: `docs/evidence/rescue/R5_GRAPHICAL_ASSETS_STAGE.md`

---

## Phase 4 — Controlled ISO Build

**Nur nach Gate + Operator-Freigabe.**

Bestehende Skripte (Operator):

1. Preflight (`validate-controlled-live-build-tree.sh`, dpkg preflight)
2. Controlled build (`prepare-controlled-live-build-tree.sh` + `lb build` oder Projekt-Runbook)
3. ISO-Pfad und Größe dokumentieren

Evidence: `docs/evidence/rescue/R5_CONTROLLED_ISO_BUILD_RESULT.md`

---

## Phase 5 — SquashFS prüfen

Nach Build — Listing/contains prüfen:

| Artefakt | Erwartung |
|----------|-----------|
| `chromium` oder `x-www-browser` | vorhanden |
| `xserver-xorg` / `Xorg` | vorhanden |
| `openbox` | vorhanden |
| `/usr/local/sbin/setuphelfer-rescue-kiosk-start` | vorhanden |
| `/usr/local/sbin/setuphelfer-rescue-evidence.py` | vorhanden |
| `/usr/share/setuphelfer/rescue/ui/rescue.html` | vorhanden |

Evidence: `docs/evidence/rescue/R5_SQUASHFS_CONTENT_CHECK.md`

---

## Phase 6 — GRUB Theme nach Build

```bash
./scripts/rescue-live/verify-rescue-grub-theme.sh
```

Erwartung: `grub.cfg` enthält Theme-Referenz; Exit 0 oder dokumentierte WARN.

Evidence: `docs/evidence/rescue/R5_GRUB_THEME_POST_BUILD.md`

---

## Phase 7 — ISO SHA256

```bash
sha256sum <iso-path> > docs/evidence/rescue/R5_ISO_SHA256.txt
```

In `telemetry`/Build-Summary referenzieren.

---

## Phase 8 — Stick-Ziel erkennen

**Kein Schreiben ohne Freigabe.**

```bash
lsblk -o NAME,SIZE,TYPE,TRAN,MODEL,VENDOR,MOUNTPOINT
# Nur Setuphelfer-Rettungsstick als Ziel — nie interne NVMe
```

Evidence: `docs/evidence/rescue/R5_USB_TARGET_IDENTIFICATION.md`

---

## Phase 9 — USB-Write (Operator)

**Explizite Freigabe erforderlich.**

- Ziel-USB eindeutig
- Pre/Post `lsblk`, `blkid`
- Schreibprotokoll + Hash-Abgleich

Evidence: `docs/evidence/rescue/R5_USB_WRITE_OPERATOR_RESULT.md`

---

## Phase 10 — MSI-Boot

Hardware: MSI-Rechner (Zielsystem)

Nach Boot:

```bash
setuphelfer-rescue-evidence.py detect
setuphelfer-rescue-evidence.py bundle
setuphelfer-rescue-kiosk-health
cat .../matrix/rescue_test_matrix_latest.md
```

Evidence: `docs/evidence/rescue/R5_MSI_BOOT_RESULT.md`

---

## Phase 11 — Evidence auf Stick prüfen

Erwartete Struktur:

```text
/setuphelfer-evidence/
  boot/
  menu/
  hardware/
  rescue-ui/kiosk_report_latest.json
  matrix/rescue_test_matrix_latest.md
  telemetry/spool/
  summaries/rescue_evidence_latest.md
```

Prüfen: kein RAM-Fallback wenn Stick writable.

Evidence: `docs/evidence/rescue/R5_STICK_EVIDENCE_VERIFY.md`

---

## Phase 12 — Testmatrix auswerten

`matrix/rescue_test_matrix_latest.md` — mindestens bewerten:

| ID | Erwartung R.5 |
|----|----------------|
| R4-BROWSER-PKG-001 | green (runtime: Browser läuft) |
| R4-KIOSK-001 | green oder yellow |
| R3-PERSIST-001 | green (kein Fallback) |
| R3-INTERNAL-001 | green |
| R3-RESTORE-001 | blocked |

Evidence: `docs/evidence/rescue/R5_MATRIX_EVALUATION.md`

---

## Phase 13 — Evidence Bundle auswerten

`summaries/rescue_evidence_latest.md` — Blocker und `next_actions`.

Evidence: `docs/evidence/rescue/R5_BUNDLE_EVALUATION.md`

---

## Phase 14 — Abschlussbericht

`docs/evidence/rescue/R5_CAMPAIGN_SUMMARY.md`

Pflichtfelder:

- ISO SHA256
- USB-Write ja/nein + Operator
- MSI-Boot Ergebnis
- Matrix-Ampeln
- Offene Blocker für R.6

---

## Erfolgskriterium

MSI bootet vom neuen Stick, Kiosk oder dokumentierter TUI-Fallback, alle relevanten Ergebnisse unter `/setuphelfer-evidence/`, Testmatrix zeigt klar nächste Aktion.

---

## Referenzen

- `docs/evidence/rescue/CAMPAIGN_R4_PROMPT.md`
- `docs/architecture/RESCUE_BROWSER_KIOSK_R4.md`
- `scripts/rescue-live/verify-rescue-grub-theme.sh`
- `backend/core/rescue_test_matrix.py` (Matrix v4)
