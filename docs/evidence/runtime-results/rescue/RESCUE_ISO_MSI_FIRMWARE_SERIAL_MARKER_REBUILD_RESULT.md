# RESCUE_ISO_MSI_FIRMWARE_SERIAL_MARKER_REBUILD_RESULT

**Datum:** 2026-06-06  
**Prompt:** `RESCUE_ISO_MSI_FIRMWARE_SERIAL_MARKER_REBUILD_OPERATOR_RUN`

## Ergebnis

**Workspace-Fix grün, ISO-Rebuild ausstehend (Operator sudo).** Intel-WLAN/BT-Firmware-Pakete und NetworkManager in der controlled Paketliste; Serial-Boot-Marker QEMU-only; Version **1.7.4.2**; Tests grün. Controlled ISO-Build **nicht** ausgeführt (Policy-Gate Exit **30**, root-owned stale `binary/`).

## Git / Version

| Feld | Vorher | Nachher |
|------|--------|---------|
| HEAD | `345187b` | Commit in Phase 11 |
| Projektversion | `1.7.4.1` | **`1.7.4.2`** |
| Live `/api/version` | `1.7.4.1` | unverändert (Deploy nicht Teil dieses Prompts) |

## Commit / Push / Deploy

| Aktion | Ergebnis |
|--------|----------|
| Commit | ja (Phase 11, selektiv) |
| Push | nein |
| Deploy nach `/opt` | nein |

## Phase 0 — Gates

| Prüfung | Ergebnis |
|---------|----------|
| `check-backend-version-gate.sh` | **OK** (Live noch 1.7.4.1) |
| `verify_deploy_to_opt --phase all` | **ok=True** |
| `/api/rescue/telemetry/health` | **200**, `status=ok` |

## Phase 1 — MSI-Boot-Evidence

Aktualisiert/abgeglichen:

- `RESCUE_USB_MSI_UEFI_BOOT_OPERATOR_RESULT.md`
- `RESCUE_USB_MSI_BOOT_FIRMWARE_AND_SERIAL_MARKER_TRIAGE.md`
- `rescue_iso_usb_gate_status_latest.json`

Klassifikation unverändert korrekt: **`partial_success`**, Stick bootet, Windows-Inspect blockiert.

## Phase 2 — Version 1.7.4.2

- `config/version.json`, `VERSION`, Root/Frontend-Pakete, `setuphelfer-version.json`
- `check_version_consistency.py`: **ok=True**
- Cargo/Tauri Semver-Projektion: **1.7.4** (patch W=2)

## Phase 3 — Paketliste (MSI)

In `prepare-controlled-live-build-tree.sh` → `setuphelfer.list.chroot`:

```text
firmware-iwlwifi
firmware-intel-sound
wireless-regdb
network-manager
```

Intel Bluetooth: **`firmware-iwlwifi`** liefert `intel/ibt-*` (korrigiert; `firmware-intel-sound` nur Sound-DSP).

## Phase 4 — Serial-Boot-Marker

`build/rescue/profiles/developer-qemu/.../setuphelfer-serial-boot-markers.service`:

- `ConditionVirtualization=qemu`
- kein `TTYPath=/dev/ttyS0`
- `StandardOutput=journal`

Validator (developer-qemu): prüft QEMU-Condition und fehlendes TTYPath.

## Phase 5 — NetworkManager / nmcli

`setuphelfer-rescue-network-menu.sh` nutzt **`nmcli`** für WLAN (Option 4). NetworkManager als Pflichtpaket aufgenommen.

## Phase 6 — Tests

| Test | Ergebnis |
|------|----------|
| `test_rescue_developer_serial_visibility_v1` | **OK** |
| `test_tauri_config_schema_v1` | **OK** (1.7.4.2) |
| `test_version_consistency_v1` | **OK** |
| `bash -n` prepare/validate | **OK** |

## Phase 7 — Build-Tree

| Schritt | Ergebnis |
|---------|----------|
| `prepare-controlled-live-build-tree.sh` | **OK** (`rescue_build_profile=standard`) |
| Pakete im Tree | **4/4** sichtbar |
| `validate-controlled-live-build-tree.sh` | **blockiert** — stale root-owned `binary/live/filesystem.squashfs` vom Vor-Build |

## Phase 8 — ISO-Rebuild

| Feld | Wert |
|------|------|
| Ausgeführt | **nein** (Agent) |
| Policy-Gate | `blocked_requires_operator_sudo_policy` |
| LB_EXIT | **30** |
| Vorherige ISO SHA256 | `09b9482a4ef18e2abf091edace794fc6baa27398f44b26e131db87ca855e0879` |
| Neue ISO SHA256 | **n/a** (Rebuild ausstehend) |
| UEFI Validator | **n/a** |

## Phase 9 — ISO-Inhalt

Nicht prüfbar ohne Rebuild. Erwartung nach Operator-Build: iwlwifi-9000-ucode + `intel/ibt-17-16-1.sfi` in Squashfs. Falls BT nach Rebuild fehlt: **`RESCUE_ISO_INTEL_BT_FIRMWARE_STILL_MISSING`**.

## Phase 10 — Blocker

### Resolved (Workspace)

- Paketliste + Validator + Serial-Marker-Fix vorbereitet

### Offen (bis Operator-Rebuild + MSI-Retest)

- `RESCUE_ISO_INTEL_WIFI_BT_FIRMWARE_MISSING`
- `RESCUE_SERIAL_BOOT_MARKERS_HARDWARE_INCOMPATIBLE` (wirksam nach Rebuild)
- `RESCUE_TARGET_NETWORK_TELEMETRY_NOT_VALIDATED`
- `WINDOWS_INSPECT_BLOCKED_UNTIL_LIVE_NETWORK_VALIDATED`

## Erfolgskriterien

**Nicht vollständig grün** — ISO-Rebuild + UEFI-Validator + Squashfs-Nachweis ausstehend.

## Operator — verbleibende Schritte

```bash
cd /home/volker/piinstaller

sudo bash scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
./scripts/rescue-live/prepare-controlled-live-build-tree.sh
./scripts/rescue-live/validate-controlled-live-build-tree.sh \
  build/rescue/live-build/setuphelfer-rescue-live

export RESCUE_MSI_FIRMWARE_REBUILD_FREIGEGEBEN=1
sudo ./scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build

ISO=build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso
sha256sum "$ISO"
./scripts/rescue-live/validate-rescue-iso-uefi-boot.sh "$ISO"
```

Danach: **`RESCUE_USB_REWRITE_OPERATOR_AFTER_MSI_FIRMWARE_REBUILD`**

## Nicht ausgeführt

USB-dd, MSI erneut gebootet, Windows-Inspect, apt auf Host, Push, Deploy

## Follow-up (2026-06-06)

Operator-Rebuild mit `1.7.4.2` scheiterte mit **`LB_EXIT=123`** — Paketnamen korrekt, aber live-build nur **`main`**. Fix in **`1.7.4.3`**: Archive-Areas `main contrib non-free-firmware`. Intel-BT (`intel/ibt-*`) über **`firmware-iwlwifi`**, nicht `firmware-intel-sound`. Siehe `RESCUE_ISO_NON_FREE_FIRMWARE_COMPONENT_FIX_RESULT.md`.

## Follow-up Build-Validierung (1.7.4.4, SHA `dc351387…`)

LB_EXIT=0 · iwlwifi-9000 + ibt-17-16-1 im SquashFS ✓ · UEFI Exit 34 ✗ · nmcli fehlt ✗ · Details: `RESCUE_ISO_BUILD_SUCCESS_VALIDATION_RESULT.md`

## Secrets

Keine Token-Werte in dieser Datei.
