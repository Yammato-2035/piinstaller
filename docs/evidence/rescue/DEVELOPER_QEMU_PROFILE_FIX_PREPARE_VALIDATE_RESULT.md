# Developer QEMU Profile Fix — Prepare/Validate Result (Phase 7–8)

**Datum:** 2026-06-02

## Exit-Codes

| Schritt | Exit | Log |
|---------|------|-----|
| Prepare (`SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu`) | **0** | `developer_qemu_profile_prepare_latest.log` |
| Validate | **11** | `developer_qemu_profile_validate_latest.log` |

### Validate-Blocker

```
FORBIDDEN: build/rescue/live-build/setuphelfer-rescue-live/binary/live/filesystem.squashfs
```

Artefakte vom vorherigen **Standard-Profil**-Build (root-owned, 2026-06-02 21:58). Entfernung in Agent-Session ohne `sudo` nicht möglich. Operator-Rebuild beginnt mit `sudo ./auto/clean`.

## Bootappend nach Prepare

**Vorher (Standard-Profil, fehlgeschlagener Smoke):**
```
quiet splash init=/lib/systemd/systemd
```

**Nachher (developer-qemu Prepare):**
```
init=/lib/systemd/systemd console=tty0 console=ttyS0,115200n8 …
```
(kein `quiet splash`)

Log: `developer_qemu_profile_bootappend_after_prepare_latest.log`

## Manifest

```json
{
  "rescue_build_profile": "developer-qemu",
  "qemu_serial_console_configured": true,
  "qemu_smoke_autopilot_hook": true,
  "qemu_guest_devserver_endpoint": "http://10.0.2.2:8001"
}
```

## Services

| Service | Im Tree | Enabled/Wanted (Prepare-only) | Enable-Mechanismus |
|---------|---------|-------------------------------|-------------------|
| `setuphelfer-qemu-smoke-autopilot.service` | yes | static wants: **no** | Hook 090 beim Chroot-Build |
| `setuphelfer-dev-agent.service` | yes (Bundle) | **no** (developer-qemu) | Autopilot übernimmt Report |

## Profilgrenze

- **Standard:** `quiet splash`, kein Hook 090, kein Serial-ISOLINUX
- **developer-qemu:** Serial + Autopilot-Hook; Preflight-Guard in Autopilot-Smoke

## Status

**review_required**

Profil-Fix materialisiert und manuell verifiziert; Validate Exit 11 durch stale binary-Artefakte. Nach Operator-`sudo ./auto/clean` → Validate Exit 0 erwartet → dann **ready_for_developer_qemu_iso_rebuild**.

Nächster Schritt: **DEVELOPER QEMU ISO REBUILD OPERATOR RUN** (mit `developer-qemu`-Profil).
