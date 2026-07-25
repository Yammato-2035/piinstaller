# PI-RS-INSTALL-ASSISTANT-001 — Zug A0 Disk-Rollenbindung

## Ziel

Stabile Disk-Rollen ohne Identität allein über `/dev/nvmeXnY`.

## Rollen

| Rolle | Default |
|-------|---------|
| `windows_system` | write blocked |
| `linux_target` | Write nur nach Bind + Freigabe (API: immer `write_allowed=false` bis Handoff) |
| `rescue_usb` | nur USB-Updater-Gates; nie Mint-Ziel |

## Identität

Modell + `serial_hash` + Größe + PCI-Hint (+ optional NGUID/EUI64).  
Device-Pfad darf sich ändern (`resolve_role_after_device_rename`).

## Module

- `backend/core/rescue_nvme_install_target.py`
- Template: `config/rescue/asus_rog_install_targets.template.json`
- API: `/api/rescue/install-assistant/storage/*`

## Tests

`backend/tests/test_rescue_install_assistant_001_v1.py` — `DiskRoleBindTests`

## Ergebnis

- Gleicher Fingerprint bei Device-Namen-Drift: ok
- Falscher Hash: blockiert
- Rescue-Stick (USB / SETUPHELFER-Label): ausgeschlossen als `linux_target`
