# RS-001 React Rescue SquashFS Content Check

**Datum:** 2026-06-09  
**HEAD:** `27b0829` (uncommitted Integration/Repack)  
**Squashfs:** `build/rescue/filesystem.squashfs.repacked-1.7.10.0`  
**SHA256:** `a54aae1d902523cf08b37105b1f6001e048d610b57210520ea2e1a649b3fe820`  
**Quelle:** Repack von `filesystem.squashfs.repacked-1.7.9.3` (`ac95ebc3…`)

## Build-Modus

| Feld | Wert |
|------|------|
| Controlled `lb build` | **blocked** (`sudo` Passwort erforderlich) |
| Repack-Skript | `scripts/rescue-live/repack-rescue-squashfs-react-shell.sh` |
| `build_status` | **success** (Repack) |
| `contains_react_rescue_shell` | **true** |

## Pflichtbefund (unsquashfs -ll)

| Check | Status |
|-------|--------|
| React Rescue UI (`rescue.html`) | **ok** |
| `rescue-ui-manifest.json` | **ok** |
| `setuphelfer-rescue-ui.service` | **ok** |
| `setuphelfer-rescue-state.service` | **ok** |
| `setuphelfer-rescue-evidence-spool.service` | **ok** |
| `rescue_offline_first_policy.py` | **ok** |
| `rescue_evidence_spool.py` | **ok** |
| `rescue_machine_profile.py` | **ok** |
| `rescue_boot_status.py` | **ok** |
| UI ohne `Requires=network-online.target` | **ok** |
| Telemetry Boot-Blocker | **false** |
| Version im Payload | **1.7.10.0** (`opt/setuphelfer-rescue/VERSION`) |

## Startpfad

- Default-GRUB behält `setuphelfer_start_assistant=1`
- `setuphelfer-rescue-start-assistant --boot-trigger` delegiert an `setuphelfer-rescue-ui-launch`, wenn `rescue.html` vorhanden
- Whiptail-Hauptmenü wird übersprungen, wenn React UI im SquashFS liegt

## Offen

- Kein JS-fähiger Browser im SquashFS — Hardware-Anzeige der React-Oberfläche auf tty1 **nicht bewiesen**
- Controlled ISO-Build mit `lb build` ausstehend (Operator-Terminal + sudo)
