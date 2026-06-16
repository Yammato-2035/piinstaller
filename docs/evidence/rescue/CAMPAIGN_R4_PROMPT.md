# Kampagne R.4 — Browser/Display/Kiosk + Controlled ISO + MSI Boot Test

**Voraussetzung:** R.3 committed (`feat(rescue): add persistent logging and test matrix`, Version `1.7.16.0`)

---

## Ziel

Rettungsstick auf MSI-Rechner belastbar booten und alle R.3-Ergebnisse auf dem Stick verifizieren — inklusive grafischem Menü/Kiosk-Pfad.

---

## Ziele (10)

1. **Browser + Display-Stack** in `setuphelfer.list.chroot` aufnehmen (Build-Konfiguration, kein `apt install` auf Host)
2. **Kiosk-Autostart** vorbereiten (systemd user service / Launch-Skript)
3. **Grafisches GRUB** im fertigen `grub.cfg` verifizieren (Theme aktiv, Assets im Binary-Image)
4. **`setuphelfer-rescue-telemetry-push`** an Telemetrie-Spool anbinden (`rescue_telemetry_spool.py`)
5. **Controlled ISO Build** (nach Gate, Operator-geführt)
6. **Stick schreiben** nur nach expliziter Operator-Freigabe
7. **MSI-Boot** durchführen (Hardware)
8. **`/setuphelfer-evidence/`** vom Stick prüfen (Persistenz, kein RAM-Fallback wenn möglich)
9. **Testmatrix** auswerten (`matrix/rescue_test_matrix_latest.md`)
10. **Rescue Evidence Bundle** auswerten (`summaries/rescue_evidence_latest.md`)

---

## Harte Sicherheitsregeln

| Verboten | Erlaubt |
|----------|---------|
| Restore / Backup-Execute | Read-only MSI-Diagnose |
| Partition-Write / Format | Evidence auf erkanntem Rettungsstick |
| rw-Mount interne NVMe/HDD/SSD | Controlled ISO Build (isoliert) |
| Deploy ohne Gate | USB-Write **nur** mit Operator-Freigabe |
| `apt install` auf Host | Package-Liste im live-build tree ändern |
| `systemctl restart` auf Host | Unit-Tests, Build-Vorbereitung |

**ISO-Build:** nur nach `./scripts/check-runtime-deploy-gate.sh` (oder Profil-Gate) und Phase-0-Dokumentation.

**USB-Write:** nur wenn Stick eindeutig als Setuphelfer-Rettungsstick erkannt; Operator bestätigt Zielgerät.

**Interne Datenträger:** read-only — Matrix-Eintrag `R3-INTDISK-*` muss `green` bleiben.

---

## Phase 0 — Gate & Status

```bash
git status --short
git branch --show-current
git rev-parse --short HEAD
./scripts/check-runtime-deploy-gate.sh || true
./scripts/check-module-boundaries.sh || true
```

Evidence: `docs/evidence/rescue/R4_PHASE0_STATUS.md`

---

## Phase 1 — Package-Liste (Browser/Display)

Datei: `build/rescue/live-build/setuphelfer-rescue-live/config/package-lists/setuphelfer.list.chroot`

**Vorschlag (minimaler Kiosk-Stack):**

- `chromium` oder `firefox-esr` (eine Variante, dokumentierte Wahl)
- `xorg` + `openbox` (oder `lxqt` — Entscheidung dokumentieren)
- `xdotool` (optional, Kiosk-Fokus)

**Nicht:** `apt install` auf Entwicklungs-Host.

Evidence: `docs/evidence/rescue/R4_PACKAGE_LIST_BROWSER_DISPLAY.md`

---

## Phase 2 — Kiosk-Autostart

Prüfen/ergänzen:

- `scripts/rescue-live/image/setuphelfer-rescue-ui-launch`
- systemd user service unter `config/includes.chroot/etc/systemd/user/`
- Autostart-Hook in `setuphelfer-rescue-start-assistant` oder dediziertem `setuphelfer-rescue-kiosk-autostart`

Fallback: TUI bleibt aktiv wenn Browser/Display fehlt.

Evidence: `docs/evidence/rescue/R4_KIOSK_AUTOSTART_R4.md`

---

## Phase 3 — GRUB Theme Verifikation

Prüfen nach Build:

- `stage-rescue-graphical-assets.sh` Output im Binary-Image
- `boot/grub/themes/setuphelfer/theme.txt` + PNG im ISO
- `grub.cfg` referenziert Theme

Evidence: `docs/evidence/rescue/R4_GRUB_THEME_VERIFY.md`

Matrix-Feature-Tabelle aus R.3-Audit aktualisieren.

---

## Phase 4 — Telemetrie-Spool ↔ Push

Datei: `scripts/rescue-live/image/setuphelfer-rescue-telemetry-push` (oder äquivalent)

Anbindung:

- `write_telemetry_event()` bei Upload-Fehler
- `mark_telemetry_event_sent()` bei Erfolg
- `list_pending_telemetry_events()` beim Menüstart

Evidence: `docs/evidence/rescue/R4_TELEMETRY_SPOOL_INTEGRATION.md`

Tests: `backend/tests/test_rescue_telemetry_spool_r4_integration.py` (optional)

---

## Phase 5 — Controlled ISO Build

Voraussetzungen:

- Phase 0 bestanden
- Package-Liste + Kiosk + GRUB-Staging committed
- Kein Deploy in gleicher Session ohne Freigabe

Ablauf (Operator):

1. `stage-rescue-graphical-assets.sh`
2. Controlled build preflight (bestehende Skripte)
3. ISO bauen
4. ISO validieren (`isoinfo`, SquashFS-Listing)

Evidence: `docs/evidence/rescue/R4_CONTROLLED_ISO_BUILD_RESULT.md`

---

## Phase 6 — Stick schreiben (Operator)

**Nur mit expliziter Freigabe.**

- Ziel-USB eindeutig identifizieren
- Kein internes NVMe/SSD als Ziel
- Schreibprotokoll + Hash

Evidence: `docs/evidence/rescue/R4_USB_WRITE_OPERATOR_RESULT.md`

---

## Phase 7 — MSI-Boot

Hardware: MSI-Rechner (Zielsystem aus Auftrag)

Nach Boot prüfen:

```bash
setuphelfer-rescue-evidence.py detect
setuphelfer-rescue-evidence.py bundle
ls -la /run/live/medium/setuphelfer-evidence/  # oder Media-Mount
cat .../matrix/rescue_test_matrix_latest.md
```

Evidence: `docs/evidence/rescue/R4_MSI_BOOT_RESULT.md`

---

## Phase 8 — Matrix & Bundle Auswertung

Auswerten:

| Bereich | Erwartung |
|---------|-----------|
| Boot | green |
| Stick-Persistenz | green (kein RAM-Fallback) |
| TUI-Menü | green |
| Browser/Kiosk | green oder yellow (erster Build) |
| MSI-Diagnose | green |
| Interne Disks read-only | green |
| Restore-Gate | blocked |

Evidence: `docs/evidence/rescue/R4_MATRIX_EVALUATION.md`

---

## Phase 9 — Abschluss & Version

Bei erfolgreicher Verifikation:

- Version-Bump nur wenn neue Funktionsversion (z. B. Kiosk aktiv = `1.7.17.0`)
- Commit gezielt, kein `git add -A`

Abschlussbericht: `docs/evidence/rescue/R4_CAMPAIGN_SUMMARY.md`

---

## Erfolgskriterium

Nach MSI-Boot liegen auf dem Stick:

```text
/setuphelfer-evidence/
  boot/
  menu/
  hardware/msi_diagnostics_latest.json
  matrix/rescue_test_matrix_latest.md
  summaries/rescue_evidence_latest.md
  telemetry/spool/
```

Testmatrix zeigt klar: was funktioniert, was blockiert, nächste Aktion.

---

## Referenzen R.3

- `backend/core/rescue_persistence.py`
- `backend/core/rescue_test_matrix.py`
- `backend/core/rescue_evidence_bundle.py`
- `docs/evidence/rescue/GRAPHICAL_BOOT_AND_KIOSK_AUDIT_R3.md`
- `docs/architecture/RESCUE_STICK_LOGGING_AND_TESTMATRIX_R3.md`
