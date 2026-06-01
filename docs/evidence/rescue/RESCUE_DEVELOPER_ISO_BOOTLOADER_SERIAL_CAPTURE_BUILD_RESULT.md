# Developer Rescue ISO — Bootloader Serial Capture Rebuild

**Stand:** 2026-06-01
**HEAD:** `ede7784`
**Branch:** `main`
**Repository:** PUBLIC (`Yammato-2035/piinstaller`)
**Push allowed:** no
**Push durchgeführt:** no
**NDA risk:** blocked (public repository)

## Zusammenfassung

| Phase | Ergebnis |
|-------|----------|
| Profil-Gate vor Build | **OK** — `install_profile=release`, Exit 0 |
| Dependency-Preflight | **OK** |
| Alte ISO dokumentiert | **yes** — SHA `be016f2a…` (vor Commit `2e0216f`) |
| Clean (`--operator-confirm-clean`) | **blocked** — `sudo` Passwort in Agent-Session |
| Prepare `developer-qemu` | **OK** |
| Controlled ISO Build | **blocked** — kein `lb build` ausgeführt |
| Neue ISO | **nein** — SHA unverändert |

## Bootloader-Fix-Kontext

Commit **`2e0216f`** (Ancestor von HEAD): QEMU chardev/isa-serial, ISOLINUX `SERIAL`/`TIMEOUT 30`/`DEFAULT live-`, GRUB-Serial-Hook in `prepare-controlled-live-build-tree.sh`. Die vorhandene ISO (`mtime` 2026-06-01 17:28) wurde **vor** diesem Fix gebaut; `strings` auf der ISO zeigt **kein** `SERIAL 0 115200` / `TIMEOUT 30`.

## Profil-Gate (vor Build)

```json
{
  "install_profile": "release",
  "project_version": "1.7.3.0",
  "profile_gate_exit": 0
}
```

## Build-Versuche

| Run-ID | Policy | Exit | `error_code` | `build_started` |
|--------|--------|------|--------------|-----------------|
| `rescue_developer_iso_20260601_bootloader_serial_capture` | blocked (kein TTY) | **30** | `blocked_requires_operator_sudo_policy` | false |
| `rescue_developer_iso_20260601_bootloader_serial_capture_tty` | ready (pseudo-TTY) | **34** | `rescue_iso_build.permission_denied_dot_build` | false |

**Nächster Operator-Schritt (interaktives Terminal mit sudo):**

```bash
cd /home/volker/piinstaller
export SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu
sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
./scripts/rescue-live/prepare-controlled-live-build-tree.sh
./scripts/rescue-live/run-controlled-iso-build-with-logging.sh \
  --operator-confirm-build \
  --profile developer-qemu \
  --run-id rescue_developer_iso_20260601_bootloader_serial_capture
```

## ISO-Artefakt (unverändert)

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| Größe | 511705088 B |
| mtime | 2026-06-01 17:28:49 |
| **old_iso_sha256** | `be016f2adacfc9906b4b92ca8ab0d6b0390ad1e39a1e2cbb1f0a98eb35241a3f` |
| **new_iso_sha256** | *(kein neuer Build)* — gleich wie oben |
| **new_iso_differs_from_old** | **no** |

## Prepare-Tree (developer-qemu, statisch)

| Prüfung | Tree |
|---------|------|
| ISOLINUX `SERIAL 0 115200` | **yes** (`config/bootloaders/isolinux/isolinux.cfg`) |
| `TIMEOUT 30` | **yes** |
| `DEFAULT live-` / `ONTIMEOUT live-` | **yes** |
| GRUB Serial-Hook | **yes** (`config/hooks/normal/095-developer-qemu-grub-serial.hook.binary`) |
| `console=tty0` | **yes** |
| `console=ttyS0,115200n8` | **yes** |
| `quiet`/`splash` im Developer-Append | **no** |
| Autopilot/Agent-Marker im Live-Build-Tree | **no** (nur unter `build/rescue/profiles/developer-qemu/`) |

## Guardrails

Kein QEMU-Lauf, kein USB/dd, kein Backup/Restore, kein apt, kein Push, kein `git add -A` für Build-Artefakte.

## QEMU-Smoke-Retry Status

**`blocked`** — ISO-Rebuild nach Bootloader-Fix ausstehend (Operator-sudo erforderlich).
