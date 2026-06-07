# RESCUE Start Assistant — Post-Build Validation

**Datum:** 2026-06-07  
**Prompt:** `RESCUE_START_ASSISTANT_POST_BUILD_VALIDATION_AND_USB_REWRITE_HANDOFF`  
**Workspace:** `1.7.7.0` · **HEAD:** `745eb2f` (vor Evidence-Commit)  
**Branch:** `main`  
**Build:** `LB_EXIT=0` · **UEFI post-patch:** `patch_rc=0 validate_exit=0`

## Ergebnis

**Post-Build-Validierung grün.** Start Assistant, WLAN-Onboarding, Telemetrie-Automatisierung, Disk-Discovery, Plan-Builder, Branding und korrigiertes Boot-Menü sind in der ISO nachweisbar.

**USB-Rewrite-Handoff freigegeben** — kein dd durch Agent; Readback und MSI-Retest bleiben Operator-Pflicht.

| Prüfung | Ergebnis |
|---------|----------|
| ISO vorhanden | ja |
| ISO SHA256 | `3fe6628a1316b2ceaa2850748e47a2e9c8984266a92d541e7d2aa29f80d2dbf7` |
| ISO Größe | 683671552 bytes (~652 MiB) |
| ISO Typ | ISO 9660 bootable `SETUPHELFER_RESCUE` |
| UEFI-Validator | **Exit 0** (BIOS + EFI_ELTORITO + BOOTX64 + EFI_IMG) |
| Boot-Menü / Branding | **ja** (MENU TITLE + alle Custom-Labels) |
| Start Assistant im SquashFS | **ja** |
| Network-Onboarding im SquashFS | **ja** |
| Telemetrie-Push im SquashFS | **ja** (+ retry timer) |
| Disk-Discovery / Plan-Builder | **ja** |
| Shell/Python-Syntax | **ja** (bash -n + py_compile) |
| Unit-Tests | **15/15 OK** |
| Telemetrie-LAN-Proxy | läuft, Health 200, Dev-Pfade 404 |

## Phase 0 — Repo/Gates

| Check | Ergebnis |
|-------|----------|
| `check_version_consistency.py` | OK (workspace `1.7.7.0`) |
| `check-backend-version-gate.sh` | Exit 14 — API `1.7.4.1` vs Workspace `1.7.7.0` (Runtime-Drift, kein ISO-Blocker) |
| `check-packaging-version-gate.sh` | OK (Warn stale bundles) |
| `controlled_iso_build_latest_summary.json` | `exit_code=0`, `LB_EXIT=0`, `UEFI_POST_PATCH: patch_rc=0 validate_exit=0` |

## Phase 1 — ISO-Basis

```text
-rw-r--r-- 652M binary.hybrid.iso
SHA256=3fe6628a1316b2ceaa2850748e47a2e9c8984266a92d541e7d2aa29f80d2dbf7
file: ISO 9660 CD-ROM filesystem data (bootable) 'SETUPHELFER_RESCUE'
```

## Phase 2 — UEFI/BIOS

```text
validate-rescue-iso-uefi-boot.sh → Exit 0
OK: rescue ISO UEFI-x64 — BIOS=true EFI_ELTORITO=true BOOTX64=true EFI_IMG=true
```

Post-Patch-Artefakte in Build-Log bestätigt; Validator nach Patch erneut Exit 0.

## Phase 3 — Boot-Menü / Branding

**isolinux.cfg:** `MENU TITLE Setuphelfer Rettungsstick`, `MENU BACKGROUND /bootlogo`, `splash.png` vorhanden.

**live.cfg — nachgewiesene Einträge:**

| Eintrag | Status |
|---------|--------|
| Setuphelfer Rettung starten | ja (`setuphelfer-rescue-default`, menu default) |
| Netzwerk-Assistent | ja (`setuphelfer-rescue-network`) |
| MSI/NVIDIA-Kompatibilitätsmodus | ja (`setuphelfer-rescue-msi-compat`, `pci=noaer nomodeset`) |
| Diagnosemodus | ja (`setuphelfer-rescue-diagnose`) |
| Start in RAM / Media-Check | ja (`setuphelfer-rescue-toram`, `toram`) |
| Neustart | ja (`reboot.c32`) |
| Herunterfahren | ja (`poweroff.c32`) |

**Branding:** `/usr/share/setuphelfer/rescue/boot-branding.txt` im SquashFS (ASCII-Logo + Tagline).

## Phase 4 — SquashFS-Komponenten

Alle Pflichtkomponenten unter `usr/local/sbin/` bzw. `usr/share/setuphelfer/rescue/`:

- setuphelfer-rescue-start-assistant
- setuphelfer-rescue-network-onboarding
- setuphelfer-rescue-telemetry-push + telemetry-build-payload.py
- setuphelfer-rescue-media-check
- setuphelfer-rescue-disk-discovery (+ .py)
- setuphelfer-rescue-plan-builder.py
- setuphelfer-rescue-task-pull
- setuphelfer-rescue-common.sh
- boot-branding.txt

**Netzwerk:** nmcli, NetworkManager (enabled), rfkill (`/usr/sbin`), iw (`/usr/sbin`), ping, curl, regulatory.db-debian.

**Firmware:** iwlwifi-9000-pu-b0-jf-b0-*, intel/ibt-17-16-1.sfi.

**Systemd (multi-user.target.wants):** start-assistant, network-onboarding, telemetry-push, media-check, task-pull; telemetry-retry.timer in timers.target.wants.

**QEMU-Serial:** setuphelfer-serial-boot-markers.service mit `ConditionVirtualization=qemu`, kein aktiver `TTYPath=/dev/ttyS0`.

## Phase 5 — Syntax & Tests

```text
bash -n: alle Rescue-Shell-Skripte OK
py_compile: telemetry-build-payload.py, plan-builder.py OK
telemetry-push: kein json.loads("""...""")-Muster
python3 -m unittest test_rescue_start_assistant_v1.py test_rescue_live_telemetry_scripts_v1.py → 15 tests OK
```

## Phase 6 — Startassistent-Logik (read-only)

| Anforderung | Nachweis |
|-------------|----------|
| WizardState JSON | start-assistant schreibt State mit `write_actions_allowed: false` |
| Disk-Discovery read-only | classify_node/rescue_stick-Test OK |
| Plan-Builder (backup/restore/repair/install) | build_plans liefert alle vier Pläne |
| write_actions_allowed false | hardcoded im Start-Assistant |
| instabiles Medium blockiert Repair/Install | test_plan_builder_blocks_unstable_media OK |
| Rettungsstick nicht als Systemziel | classify rescue_stick OK |
| Anfänger-Hauptmenü (6 Einträge + Expertenmodus) | whiptail-Menü im Script verifiziert |

## Phase 7 — Telemetrie-Proxy

| Endpoint | HTTP |
|----------|------|
| `/api/rescue/telemetry/health` | 200 |
| `/api/version` | 404 |
| `/openapi.json` | 404 |
| `/api/dev-dashboard/status` | 404 |
| `/api/rescue/telemetry/v1/ingest` (GET) | 404 (POST-only, erwartet) |

Proxy: `192.168.178.140:8001`, `running=true`, `secrets_exposed=false`.

## ISO-Vergleich (Stick noch alt)

| Feld | Stick (alt) | Build (neu) |
|------|-------------|-------------|
| SHA256 | `80508492a8f3187e79bb700675d81eac3e19f8e5647bb5b4a84febcf6c8b32f0` (gate) / `09b9482a…` (operator selection) | `3fe6628a…` |
| Größe | 683671552 | 683671552 |

Stick `/dev/sdb` enthält noch ältere ISO — Rewrite ausstehend.

## Gate-Status (ehrlich)

| Feld | Wert |
|------|------|
| iso_post_build_validated | **true** |
| iso_uefi_validated | **true** |
| boot_menu_branding_validated | **true** |
| start_assistant_present_in_iso | **true** |
| network_onboarding_present_in_iso | **true** |
| telemetry_push_present_in_iso | **true** |
| disk_discovery_present_in_iso | **true** |
| plan_builder_present_in_iso | **true** |
| usb_stick_matches_current_iso | **false** |
| usb_stick_written | **false** |
| usb_write_sha256_verified | **false** |
| target_laptop_booted_from_stick | **false** |
| target_network_telemetry_validated | **false** |
| windows_inspect_executable | **false** |
| usb_rewrite_handoff_ready | **true** |

## Warnungen (kein Fake-Green, kein USB-Blocker)

1. **RUNTIME_DEPLOY_DRIFT** — Backend API `1.7.4.1` vs Workspace `1.7.7.0`; blockiert ISO-Validierung nicht.
2. **rfkill/iw unter `/usr/sbin`** statt `/usr/bin` — vorhanden und funktionsfähig.
3. **Runtime-Bundle in SquashFS** (`/opt/setuphelfer-rescue`) kann ältere Projektversion tragen; Overlay-Scripts/Units aus Build-Tree 1.7.7.0.

## Nächster Schritt

`RESCUE_USB_REWRITE_AFTER_START_ASSISTANT_ISO_OPERATOR_RUN` — siehe `RESCUE_USB_REWRITE_AFTER_START_ASSISTANT_HANDOFF.md`

## Nicht ausgeführt

dd, USB-Schreiben, MSI-Boot, Windows-Inspect, Backup, Restore, Push, Secrets geloggt.
