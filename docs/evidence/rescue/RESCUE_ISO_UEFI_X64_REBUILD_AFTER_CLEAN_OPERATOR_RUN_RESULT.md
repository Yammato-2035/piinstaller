# RESCUE_ISO_UEFI_X64_REBUILD_AFTER_CLEAN_OPERATOR_RUN

**Status:** `rescue_iso_rebuild_failed`  
**Root cause:** `blocked_requires_operator_sudo_policy` — Cursor-Agent-Shell ohne interaktives sudo; `lb build noauto` startete nicht.

**Datum:** 2026-06-05T22:45+02:00

## Phase 0 — Repo/Gate/Preflight

| Check | Ergebnis |
|-------|----------|
| Branch | `main` |
| HEAD vorher/nachher | `e353fc6` / `e353fc6` |
| `check-backend-version-gate.sh` | Exit **0** (HTTP 200, Versionsfelder ok) |
| `lb` | `/usr/bin/lb` |
| `xorriso` | `/usr/bin/xorriso` |
| `grub-mkstandalone` | `/usr/bin/grub-mkstandalone` |
| `mformat` / `mtools` | vorhanden |
| `findmnt setuphelfer-rescue-live` | keine Mounts |
| `binary.hybrid.iso` nach Clean | **iso_absent_expected_after_clean** |
| Commit | **no** |
| Push | **no** |

## Phase 1 — Prepare

| Schritt | Exit |
|---------|------|
| `RESCUE_UEFI_REBUILD_FREIGEGEBEN=1` + `prepare-controlled-live-build-tree.sh` | **0** |
| `validate-controlled-live-build-tree.sh` (mit Pfad) | **0** |
| Validator-Status | `pre_chroot_ok` — **prebuild_missing_artifacts_expected**, kein UEFI-Failure |

## Phase 2 — Controlled Rebuild

| Versuch | Ergebnis |
|---------|----------|
| Agent ohne TTY/sudo | Exit **30** `blocked_requires_operator_sudo_policy` |
| `script -qefc` + Wrapper | Policy Guard **ready**, `auto/config` ok, `sudo lb build noauto` **hing an Passwortabfrage** (Prozess beendet) |
| ISO erzeugt | **no** |
| SHA256 | — |
| `file` | — |

Summary: `docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json` (exit_code 30, build_started false beim ersten Versuch; zweiter Versuch unvollständig).

## Phase 3 — UEFI Patch/Validate

Nicht ausgeführt (ISO fehlt). Kein RESCUE-UEFI-001 als Root Cause gewertet — erwarteter Zwischenstand nach Clean.

## Phase 4 — Evidence (ISO)

| Feld | Wert |
|------|------|
| ISO vorhanden | **no** |
| SHA256 | — |
| UEFI Validator Exit | — (ISO fehlt → Exit 31 erwartet) |
| BOOTX64.EFI | **no** |
| EFI-El-Torito | **no** |
| Patch notwendig | unbekannt (Build nicht abgeschlossen) |
| USB geschrieben | **no** |
| MSI-Laptop gebootet | **no** |
| Windows-Inspect | **no** |

## Operator-Fortsetzung (Pflicht: echtes Terminal + sudo)

```bash
cd /home/volker/piinstaller
export RESCUE_UEFI_REBUILD_FREIGEGEBEN=1
sudo -v
sudo ./scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build
ISO=build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso
ls -lh "$ISO"
sha256sum "$ISO"
file "$ISO"
./scripts/rescue-live/validate-rescue-iso-uefi-boot.sh "$ISO" || true
# Bei Exit != 0 (isolinux-only):
sudo ./scripts/rescue-live/patch-rescue-iso-uefi-x64.sh --in-place "$ISO"
./scripts/rescue-live/validate-rescue-iso-uefi-boot.sh "$ISO"
xorriso -indev "$ISO" -report_el_torito as_mkisofs
xorriso -indev "$ISO" -find /EFI/BOOT/BOOTX64.EFI -type f -print 2>/dev/null || true
```

## Phase 5 — Next Prompt

**Next Prompt:** `RESCUE_ISO_UEFI_X64_REBUILD_AFTER_CLEAN_OPERATOR_SUDO_HANDOFF`  
(nach erfolgreichem Build+UEFI-Validator Exit 0 → `RESCUE_USB_WRITE_OPERATOR_FOR_WINDOWS_INSPECT`)
