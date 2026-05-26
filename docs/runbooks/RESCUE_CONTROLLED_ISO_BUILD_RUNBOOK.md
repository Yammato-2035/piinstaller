# Runbook — Controlled Rescue ISO Build

**Version:** 1.1
**real_iso_build_allowed:** `false` (bis explizite Operator-Freigabe)
**usb_write_allowed:** `false`

## Zweck

Schritt-für-Schritt-Anleitung für einen **kontrollierten** Debian-Live-ISO-Build mit integriertem Setuphelfer Temp-Runtime-Bundle — **ohne** automatische Ausführung.

## Voraussetzungen

1. **Phase 0:** `./scripts/check-runtime-deploy-gate.sh` → Exit **0**
2. **Toolcheck:** `docs/evidence/rescue/RESCUE_CONTROLLED_LIVE_BUILD_TOOL_CHECK.md` — `lb`, `xorriso`, `mksquashfs`, `grub-mkrescue` vorhanden
3. **RSVG-Preflight:** Dashboard-/Executor-Status darf **nicht** `blocked_build_tools_missing` fuer `rsvg` melden
4. **Temp-Bundle:** Validator Exit **0**
5. **Build-Tree:** `validate-controlled-live-build-tree.sh` Exit **0**
6. **Operator-Freigabe** schriftlich (Issue/Ticket/E-Mail)

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

## Dashboard-Primärweg

1. `GET /api/dev-dashboard/rescue-iso/status` oder Cockpit-Panel **Rettungsstick ISO-Build**
2. Falls stale root-owned State erkannt wird:
   - `POST /api/dev-dashboard/rescue-iso/operator-commands/sudo-clean`
3. Bundle/Tree-Schritte über:
   - `POST /api/dev-dashboard/rescue-iso/step`
4. Build nur als:
   - `POST /api/dev-dashboard/rescue-iso/operator-commands/build`
   - oder spaeter ueber `build_iso_with_sudo`, falls ein sicheres Backend-sudo-Konzept explizit aktiviert ist

Wenn `next_operator_action.type = build_dependency_required`, bleibt der Build blockiert. In diesem Fall zeigt das Dashboard nur den Operator-Hinweis fuer die fehlende Build-Abhaengigkeit, derzeit:

```bash
sudo apt install librsvg2-bin
```

Dieser Hinweis wird **nur angezeigt**, nicht automatisch ausgefuehrt.

## Konfiguration (nach Operator-Freigabe)

```bash
cd build/rescue/live-build/setuphelfer-rescue-live
./auto/config
```

**NICHT automatisch ausführen** — nur nach Freigabe.

## ISO-Build (NUR nach expliziter Operator-Freigabe)

```bash
cd build/rescue/live-build/setuphelfer-rescue-live
sudo lb build noauto
```

**NICHT automatisch ausführen**, solange das Dashboard `operator_required` meldet.

Wenn das Dashboard `build_dependency_required` oder `blocked_build_tools_missing` meldet, **kein** `lb build` starten. Zuerst die benoetigte Build-Abhaengigkeit am Build-Host bereitstellen und den Preflight erneut pruefen.

`auto/build` im Repo ist absichtlich blockiert (Exit 20).

## Erwartete Artefakte (nach Build)

- `live-image-amd64.hybrid.iso` (Pfad kann je nach live-build-Version variieren)
- SHA256 dokumentieren:

```bash
sha256sum live-image-amd64.hybrid.iso
```

## Nach Build

1. Evidence aktualisieren (`RESCUE_CONTROLLED_ISO_BUILD_RESULT.md` + Summary JSON)
2. **Kein USB-Write** in dieser Phase
3. USB-Schreiben: separater Auftrag → `RESCUE_USB_WRITE_GATE_RUNBOOK.md`

## Development Dashboard / Logs

- Status: `GET /api/dev-dashboard/rescue-iso/status` oder Cockpit-Panel **Rettungsstick ISO-Build**
- Step-Logs:
  - `build/rescue/logs/controlled-iso-build/latest.log`
  - `build/rescue/logs/controlled-iso-build/actions/<action_id>.log`
  - `build/rescue/logs/controlled-iso-build/actions/<action_id>.json`
- Summary:
  - `docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json`
- Operator muss Terminalausgaben nicht mehr manuell sammeln — Dashboard ist der Primärweg

## Aktuelle Fehlerhinweise

- stale root-owned live-build state
- `chroot_package-lists.install` stale
- `skipping ... already done`
- `tar failed` / `File exists` in `debootstrap.log`

## Clean-Hinweis

- `auto/clean` darf **kein** rekursives `lb clean` ausführen
- bevorzugter kontrollierter Clean im Build-Tree:

```bash
cd /home/volker/piinstaller/build/rescue/live-build/setuphelfer-rescue-live
sudo rm -rf .build chroot cache binary local
```

## Verboten ohne Gate

- `dd`, `mkfs`, `parted write`
- Restore, Backup, Verify Deep
- Allowlist-Erweiterung
- Safety-Gate abschwächen

## Referenzen

- `RESCUE_USB_WRITE_GATE_RUNBOOK.md`
- `RESCUE_STICK_CONTROLLED_ISO_PREPARATION_GATE.md`
- `README_SETUPHELFER_RESCUE_LIVE.md` (im Build-Tree)
