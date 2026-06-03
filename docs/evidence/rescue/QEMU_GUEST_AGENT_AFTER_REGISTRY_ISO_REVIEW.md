# QEMU Guest Agent After Registry — ISO Review

**Datum:** 2026-06-03

## ISO-Artefakt

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| Größe | ~488 MiB |
| SHA256 | `614cc86ea865608f68524ef6d905a3baa1c0b1ce3dacaa9f1b80de6f541e0784` |
| Buildprofil (Summary) | **developer-qemu** |

Artefakte:

- `qemu_guest_agent_after_registry_build_summary_latest.json`
- `qemu_guest_agent_after_registry_iso_squashfs_validator_latest.log`
- `qemu_guest_agent_after_registry_profile_fingerprint_latest.log`

## Squashfs-Validator

| Prüfung | Ergebnis |
|---------|----------|
| Exit | **0** |
| developer-qemu Autopilot-Unit enabled | **yes** |
| Bundle + systemd init | **yes** |

## Profil-Fingerprint

| Check | Ergebnis |
|-------|----------|
| `developer-qemu` bestätigt | **yes** (manifest, controlled build summary) |
| `console=ttyS0` in Bootappend | **yes** (Serial zeigt Kernel cmdline + ISOLINUX boot) |
| Autopilot in `multi-user.target.wants` | **yes** (Validator + config tree) |
| Devserver URL `http://10.0.2.2:8001` | **yes** (Unit env + autopilot script) |

## Status

**iso_profile_ok**

ISO/Profil passen zum Smoke — Fehler liegt **nach** erfolgreichem Boot/Autopilot-Start (Agent-Modul/Proxy), nicht am falschen Profil.
