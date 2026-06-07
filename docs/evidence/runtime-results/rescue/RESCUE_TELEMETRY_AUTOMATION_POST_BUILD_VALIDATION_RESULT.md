# RESCUE_TELEMETRY_AUTOMATION_POST_BUILD_VALIDATION — Ergebnis

**Datum:** 2026-06-07  
**Workspace HEAD:** `f91d2f1`  
**Version:** `1.7.6.0`

## Phase 0 — Buildstatus

| Feld | Wert |
|------|------|
| `LB_EXIT` | **0** |
| UEFI post-patch | `patch_rc=0`, `validate_exit=0` |
| Build-Summary | `controlled_iso_build_latest_summary.json` (Run `rescue_developer_iso_20260607_075741`) |
| Runtime-Drift | Workspace `1.7.6.0` vs API `1.7.4.1` (Warnung, kein ISO-Blocker) |

## Phase 1 — ISO

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| **SHA256** | **`80508492a8f3187e79bb700675d81eac3e19f8e5647bb5b4a84febcf6c8b32f0`** |
| Größe | **683671552** bytes (~652 MiB) |
| Vorherige ISO | `86cba7eb550bcdb0562a414f79d78db58c908d5d743d474365eda0bcb638e5fc` |
| Typ | ISO 9660 hybrid bootable `SETUPHELFER_RESCUE` |

Größe unverändert zur 1.7.5.0-ISO; Inhalt (Scripts/Units) geändert (neuer SHA256).

## Phase 2 — UEFI / Bootartefakte

| Prüfung | Ergebnis |
|---------|----------|
| `validate-rescue-iso-uefi-boot.sh` | **Exit 0** |
| `BOOTX64.EFI` | vorhanden |
| `boot/grub/efi.img` | vorhanden |
| `isolinux/isolinux.bin` | vorhanden |
| `isolinux/isolinux.cfg` | `MENU TITLE Setuphelfer Rescue Live` |

## Phase 3 — SquashFS Pflichtkomponenten

| Komponente | Status |
|------------|--------|
| `setuphelfer-rescue-telemetry-push` | OK |
| `setuphelfer-rescue-telemetry-build-payload.py` | OK |
| `setuphelfer-rescue-telemetry-retry` | OK |
| `setuphelfer-rescue-network-onboarding` | OK |
| `setuphelfer-rescue-media-check` | OK |
| `setuphelfer-rescue-task-pull` | OK |
| `setuphelfer-rescue-common.sh` | OK |
| `nmcli`, `NetworkManager`, `rfkill`, `iw`, `ping` | OK |
| `iwlwifi-9000*.ucode`, `intel/ibt-17-16-1.sfi`, `regulatory.db` | OK |
| systemd onboarding / telemetry-push / retry timer / media-check | OK + wants |
| `usr/share/setuphelfer/rescue/boot-branding.txt` | OK |
| `validate-rescue-iso-squashfs.sh` | **Exit 0** |

## Phase 4 — Script-Syntax / SyntaxError-Regression

| Script | bash/py | Alter Heredoc-Fehler |
|--------|---------|----------------------|
| `setuphelfer-rescue-telemetry-push` | OK | **nicht vorhanden** (ruft separates Python-Modul auf) |
| `setuphelfer-rescue-telemetry-build-payload.py` | `py_compile` OK | — |
| `setuphelfer-rescue-network-onboarding` | OK | — |
| `setuphelfer-rescue-media-check` | OK | — |
| `setuphelfer-rescue-telemetry-retry` | OK | — |
| `setuphelfer-rescue-task-pull` | bash OK | **Warnung:** enthält noch `json.loads("""$(echo …)` (separates Script, nicht Telemetrie-Push) |

**Root Cause Fix verifiziert:** Der MSI-SyntaxError (`unterminated string literal`, Zeile 31 / `lsblk`-Heredoc) kann mit dem neuen Telemetrie-Push **nicht** mehr auftreten.

## Phase 5 — Payload-Builder (trocken)

- CLI: `python3 setuphelfer-rescue-telemetry-build-payload.py /tmp/out.json` (kein `--payload-kind`; Felder fest im Modul)
- JSON gültig, `payload_kind=rescue_boot_network_telemetry`, `source=rescue_stick`, `schema_version=1`
- `payload_hash_sha256` konsistent
- Keine WLAN-Passphrasen/Tokens in Werten

## Phase 6 — Boot-Menü / Branding

| Element | Status |
|---------|--------|
| ISOLINUX MENU TITLE | **grün** |
| Text-Branding im SquashFS | **grün** |
| Custom ISOLINUX `live.cfg`-Einträge (MSI/Diagnose/toram/…) | **gelb — fehlen** (Hook `020` hat `live.cfg` nicht erweitert) |
| Custom GRUB-Menüeinträge in `boot/grub/grub.cfg` | **gelb — fehlen** (nur Default `Setuphelfer Rescue Live`) |
| Bootfähigkeit Default + systemd-Onboarding | **grün** (Onboarding/Telemetrie via systemd, nicht Menü-abhängig) |

## Phase 7 — LAN-Proxy

| Endpoint | HTTP |
|----------|------|
| `192.168.178.140:8001/api/rescue/telemetry/health` | **200** |
| `/api/version` | 404 (allowlist) |
| `/openapi.json` | 404 (allowlist) |
| `/api/fleet/sessions` | 404 (allowlist) |

## Stick-Stand (read-only)

| Feld | Wert |
|------|------|
| Gerät | `/dev/sdb` Ultra Line `24111412110212` |
| Label | `SETUPHELFER_RESCUE` (~652 MiB Partition) |
| `usb_write_sha256_verified` | **false** (Rewrite auf `80508492…` ausstehend) |

## Gate

**Post-Build ISO validiert:** ja (Telemetrie-Fix + Automation im SquashFS)  
**USB-Rewrite-Handoff:** freigegeben  
**MSI-Telemetrie-ACK / Windows-Inspect:** weiter blockiert bis physischem Retest
