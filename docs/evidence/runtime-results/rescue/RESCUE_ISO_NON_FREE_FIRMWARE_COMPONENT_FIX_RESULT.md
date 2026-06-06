# RESCUE_ISO_NON_FREE_FIRMWARE_COMPONENT_FIX_RESULT

**Datum:** 2026-06-06  
**Prompt:** `RESCUE_ISO_NON_FREE_FIRMWARE_COMPONENT_FIX_AND_REBUILD_TRIAGE`

## Ergebnis

**Workspace-Fix grün, ISO-Rebuild ausstehend (Operator sudo).** Archive-Areas korrigiert; Build-Tree-Validator grün; Version **1.7.4.3**.

## Git / Version

| Feld | Vorher | Nachher |
|------|--------|---------|
| HEAD | `4f3ca39` | Commit Phase 11 |
| Version | `1.7.4.2` | **`1.7.4.3`** |
| Commit | — | ja (selektiv) |
| Push | — | nein |
| Deploy `/opt` | — | nein |

## Fehler ingestiert

| Feld | Wert |
|------|------|
| `failure_code` | `RESCUE-ISO-FIRMWARE-APT-COMPONENT-001` |
| `lb_exit` (Operator-Versuch) | **123** |
| `root_cause` | `--archive-areas main` ohne `non-free-firmware` |
| Alte ISO SHA256 | `09b9482a4ef18e2abf091edace794fc6baa27398f44b26e131db87ca855e0879` |
| Neue ISO SHA256 | **n/a** (Rebuild ausstehend) |

## Fix

| Bereich | Änderung |
|---------|----------|
| `prepare-controlled-live-build-tree.sh` | `--archive-areas main contrib non-free-firmware` |
| Security-Archive | `main contrib non-free-firmware` |
| Validator | `RESCUE-ISO-FIRMWARE-APT-COMPONENT-001` + Paket-/NM-Codes |
| Dpkg-Preflight | `network-manager` aus Forbidden-Liste (Rescue-WLAN) |
| Doku | Intel-BT über `firmware-iwlwifi`, nicht `firmware-intel-sound` |

## Phase 6 — Tests

22/22 unittest OK, `check_version_consistency` OK, `bash -n` OK.

## Phase 7 — Prepare + Validate

| Schritt | Ergebnis |
|---------|----------|
| Prepare | **OK** |
| `non-free-firmware` in auto/config | **sichtbar** |
| Validate | **OK** (Exit 0) |

## Phase 8 — ISO-Rebuild (Agent)

| Feld | Wert |
|------|------|
| Ausgeführt | nein |
| LB_EXIT | **30** `blocked_requires_operator_sudo_policy` |
| UEFI Validator | n/a |

## Phase 9 — SquashFS

Nicht prüfbar ohne erfolgreichen Rebuild.

## Operator — verbleibend

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

SQUASH=build/rescue/live-build/setuphelfer-rescue-live/binary/live/filesystem.squashfs
unsquashfs -ll "$SQUASH" | grep -E 'iwlwifi-9000|intel/ibt-17-16-1|NetworkManager|nmcli|wireless-regdb' || true
```

## Blocker (offen)

- ISO-Rebuild + Squashfs-Firmware-Nachweis
- USB-Rewrite + MSI-Retest + Netzwerk/Telemetrie
- Windows-Inspect blockiert

## Erfolgskriterien

**Nicht vollständig grün** — ISO/Squashfs ausstehend.

## Next Prompt

**`RESCUE_ISO_MSI_FIRMWARE_REBUILD_OPERATOR_SUDO_COMPLETION`**

Danach bei Erfolg: `RESCUE_USB_REWRITE_OPERATOR_AFTER_MSI_FIRMWARE_REBUILD`

## Nicht ausgeführt

USB-dd, MSI-Retest, Windows-Inspect, apt auf Host, Deploy, Push
