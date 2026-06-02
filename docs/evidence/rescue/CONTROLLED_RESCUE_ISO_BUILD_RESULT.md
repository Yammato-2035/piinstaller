# Controlled Rescue ISO Build — Ergebnis (Ingest, NO QEMU/USB)

**Stand:** 2026-06-02  
**HEAD:** `03b60e7`  
**Run-ID:** `rescue_developer_iso_20260602_195502`  
**Status:** **`ready_for_qemu_guest_agent_smoke`**

## Build (Operator, vorheriger Lauf)

| Feld | Wert |
|------|------|
| LB_EXIT / exit_code | **0** |
| Dauer | ~224 s (21:55:02–21:58:46) |
| Profil | `standard` |
| Kein USB/dd | **yes** |

## Artefakt

| Feld | Wert |
|------|------|
| ISO | `binary.hybrid.iso` |
| Größe | 511705088 B |
| SHA256 | `505989f7d348265c08e8baeaa2971f81aa855224223859ae8d536b984dafaf52` |
| Neu nach Cleanup | **yes** (≠ Prior `52da3e018ccb…`) |

## Validierung (dieser Ingest-Lauf)

| Prüfung | Ergebnis |
|---------|----------|
| Summary ingest | **ok** |
| Squashfs-Validator | Exit **0** |
| Bundle + systemd init + enabled units | **ok** |
| Dev-Agent-Unit im Squashfs | **ok** |
| Bootmenü/splash | **ok** |
| Aktive Mounts | **none** |

## Hinweise (nicht blockierend)

- cp isolinux Wildcard-Warnungen (optionale Syslinux-Dateien)
- `rescue_agent/` Modul nicht im Temp-Bundle; `devserver_agent` vorhanden
- Chroot root-owned nach Build (erwartet)

## Kein Bootnachweis

ISO-Build LB_EXIT=0 ≠ VM-Boot ≠ USB-Write. Rescue-Stick bleibt **nicht vollständig grün** ohne QEMU-/Boot-Nachweis.

## Nächster Schritt

**QEMU GUEST AGENT SMOKE, NO USB**

JSON: `controlled_iso_build_artifact_verify_latest.json`
