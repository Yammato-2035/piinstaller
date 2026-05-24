# Runbook — Controlled Rescue ISO Build

**Version:** 1.0
**real_iso_build_allowed:** `false` (bis explizite Operator-Freigabe)
**usb_write_allowed:** `false`

## Zweck

Schritt-für-Schritt-Anleitung für einen **kontrollierten** Debian-Live-ISO-Build mit integriertem Setuphelfer Temp-Runtime-Bundle — **ohne** automatische Ausführung.

## Voraussetzungen

1. **Phase 0:** `./scripts/check-runtime-deploy-gate.sh` → Exit **0**
2. **Toolcheck:** `docs/evidence/rescue/RESCUE_CONTROLLED_LIVE_BUILD_TOOL_CHECK.md` — `lb`, `xorriso`, `mksquashfs`, `grub-mkrescue` vorhanden
3. **Temp-Bundle:** Validator Exit **0**
4. **Build-Tree:** `validate-controlled-live-build-tree.sh` Exit **0**
5. **Operator-Freigabe** schriftlich (Issue/Ticket/E-Mail)

## Vorbereitung (Repo)

```bash
./scripts/rescue-live/create-temp-runtime-bundle.sh
./scripts/rescue-live/validate-temp-runtime-bundle.sh \
  build/rescue/temp-runtime/setuphelfer-rescue-runtime
./scripts/rescue-live/prepare-controlled-live-build-tree.sh
./scripts/rescue-live/validate-controlled-live-build-tree.sh \
  build/rescue/live-build/setuphelfer-rescue-live
```

## Build-Verzeichnis

```
build/rescue/live-build/setuphelfer-rescue-live/
```

## Konfiguration (nach Operator-Freigabe)

```bash
cd build/rescue/live-build/setuphelfer-rescue-live
./auto/config
```

**NICHT automatisch ausführen** — nur nach Freigabe.

## ISO-Build (NUR nach expliziter Operator-Freigabe)

```bash
cd build/rescue/live-build/setuphelfer-rescue-live
lb build
```

**NICHT automatisch ausführen.**

`auto/build` im Repo ist absichtlich blockiert (Exit 20).

## Erwartete Artefakte (nach Build)

- `live-image-amd64.hybrid.iso` (Pfad kann je nach live-build-Version variieren)
- SHA256 dokumentieren:

```bash
sha256sum live-image-amd64.hybrid.iso
```

## Nach Build

1. Evidence aktualisieren (`RESCUE_CONTROLLED_ISO_BUILD_PREP_RESULT.md` oder separates Build-Result)
2. **Kein USB-Write** in dieser Phase
3. USB-Schreiben: separater Auftrag → `RESCUE_USB_WRITE_GATE_RUNBOOK.md`

## Development Dashboard / Logs

- Status: `GET /api/dev-dashboard/rescue-build/status` oder Cockpit-Panel **Rettungsstick Build**
- Persistente Logs (empfohlen): `scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build`
  - `build/rescue/logs/controlled-iso-build/latest.log`
  - `docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json`
- Operator muss Terminalausgaben nicht mehr manuell sammeln — Dashboard liest Evidence + Logs

## Verboten ohne Gate

- `dd`, `mkfs`, `parted write`
- Restore, Backup, Verify Deep
- Allowlist-Erweiterung
- Safety-Gate abschwächen

## Referenzen

- `RESCUE_USB_WRITE_GATE_RUNBOOK.md`
- `RESCUE_STICK_CONTROLLED_ISO_PREPARATION_GATE.md`
- `README_SETUPHELFER_RESCUE_LIVE.md` (im Build-Tree)
