# QEMU Guest Agent — Squashfs Risk Review (Post-Smoke)

**ISO:** Standard-Profil-Build (`rescue_build_profile=standard`)

| Prüfpunkt | Ergebnis |
|-----------|----------|
| devserver_agent vorhanden | **yes** |
| rescue_agent Modul | **no** |
| setuphelfer-dev-agent.service | **yes** |
| setuphelfer-qemu-smoke-autopilot.service | **yes** (Datei) |
| service enabled in multi-user.target.wants | **no** (weder dev-agent noch autopilot) |
| PYTHONPATH korrekt | **yes** (`/opt/setuphelfer-rescue`) |
| Autostart-Gap bestätigt | **yes** |
| Modul-Gap bestätigt | **yes** (`rescue_agent/` fehlt) |

## Enabled Units (Squashfs)

Nur `setuphelfer-backend.service` und `setuphelfer.service` in `etc/systemd/system/multi-user.target.wants`.

## dev-agent.env

Enthält `local_lab`, `AUTO_UPLOAD=true`, `SERVER_URL=http://10.0.2.2:8001` — aber Unit **nicht** enabled.

## Profil-Mismatch

Controlled Build lief mit **`standard`**-Profil. QEMU-Autopilot-Smoke erwartet **`developer-qemu`**:
- `console=ttyS0` in bootappend
- Autopilot-Unit-Enable via Profile-Hook

Siehe `prepare-controlled-live-build-tree.sh` Zeilen 433–476.
