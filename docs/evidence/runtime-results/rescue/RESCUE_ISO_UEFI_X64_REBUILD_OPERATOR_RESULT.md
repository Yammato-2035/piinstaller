# Rescue ISO UEFI-x64 Rebuild — Operator Run Result

**Track:** `RESCUE_ISO_UEFI_X64_REBUILD_OPERATOR_RUN`
**Status:** `blocked_by_operator_confirmation` + `blocked_requires_operator_sudo_policy`
**Agent-Lauf:** 2026-06-05 — kein Rebuild, kein Patch auf kanonischer ISO, kein USB

## Phase 0 — Gate

| Check | Ergebnis |
|--------|----------|
| HEAD | `58d8d00` (≥ erforderlich) |
| Branch | `main` |
| `check-backend-version-gate.sh` | OK |
| Pflicht-Skripte/Handoff | vorhanden |

## Phase 1 — Baseline (kanonische ISO unverändert)

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| `file` | ISO 9660, DOS/MBR boot sector, SETUPHELFER_RESCUE (bootable) |
| SHA256 | `1899f5cabf9d40c9581805def9a765557a2168fc11ac181b0f71bfc0b1ff0691` |
| Owner | `root:workspace` (Agent nicht schreibbar) |
| `validate-rescue-iso-uefi-boot.sh` | **Exit 34** — RESCUE-UEFI-001/002/003 |
| `/EFI/BOOT/BOOTX64.EFI` | **nein** |
| EFI-El-Torito | **nein** |

## Phase 2 — Build-Tree

| Schritt | Ergebnis |
|---------|----------|
| `prepare-controlled-live-build-tree.sh` | OK |
| `validate-controlled-live-build-tree.sh` | **Exit 11** — `FORBIDDEN: …/binary/live/filesystem.squashfs` (stale root-owned Build-Artefakte) |

## Phase 3 — Rebuild

**Nicht ausgeführt.**

- `RESCUE_UEFI_REBUILD_FREIGEGEBEN` = unset
- `RESCUE_SYSTEMD_REBUILD_FREIGEGEBEN` = unset
- `sudo -n` = **Passwort erforderlich** (kein Agent-sudo)

## Phase 4 — UEFI Patch

**Nicht auf kanonischer ISO ausgeführt** (root-owned, Agent nicht schreibbar).

Agent-Versuch Patch → `build/rescue/output/binary.hybrid.uefi-agent-verify.iso` scheiterte: xorriso-Extract liefert root-owned Dateien; Cleanup/Patch ohne sudo blockiert (`patch_exit=1`). **Kein Fake-Green.**

## Phase 5 — Zielzustand

| Kriterium | Status |
|-----------|--------|
| UEFI-Validator Exit 0 (kanonisch) | **nein** (34) |
| Neue SHA256 | **keine** (ISO unverändert) |
| USB geschrieben | **no** |
| MSI gebootet | **no** |
| Windows-Inspect | **blockiert** |

## Operator-Befehle (exakt, echtes Terminal)

```bash
cd /home/volker/piinstaller
export RESCUE_UEFI_REBUILD_FREIGEGEBEN=1
sudo -v

# Stale root-owned Build-State entfernen
sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean

./scripts/rescue-live/prepare-controlled-live-build-tree.sh
./scripts/rescue-live/validate-controlled-live-build-tree.sh \
  build/rescue/live-build/setuphelfer-rescue-live

cd build/rescue/live-build/setuphelfer-rescue-live
./auto/config
cd /home/volker/piinstaller

sudo env PATH="/home/volker/piinstaller/build/rescue/tool-compat/bin:$PATH" \
  RESCUE_UEFI_REBUILD_FREIGEGEBEN=1 \
  ./scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build

# live-build 3.0: UEFI-Patch mit sudo (root-owned ISO + Extract)
sudo ./scripts/rescue-live/patch-rescue-iso-uefi-x64.sh --in-place \
  build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso

./scripts/rescue-live/validate-rescue-iso-uefi-boot.sh \
  build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso
sha256sum build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso
xorriso -indev build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso \
  -report_el_torito as_mkisofs | grep -E 'isolinux|efi\.img|0xef'
xorriso -osirrox on -indev build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso \
  -find /EFI/BOOT -name BOOTX64.EFI
```

Nach **Validator Exit 0**: Evidence aktualisieren, dann erst USB-Handoff — **kein Windows-Inspect** vor MSI-UEFI-Boot.

## Next Prompt

`RESCUE_ISO_UEFI_X64_FAILURE_TRIAGE` — UEFI-Validator auf kanonischer ISO weiterhin rot; Operator sudo + Freigabe + Clean/Rebuild/Patch erforderlich.
