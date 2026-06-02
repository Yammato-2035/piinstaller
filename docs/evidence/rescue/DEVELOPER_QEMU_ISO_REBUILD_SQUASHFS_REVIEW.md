# Developer QEMU ISO Rebuild — Squashfs Review

**Datum:** 2026-06-03  
**Squashfs:** `build/rescue/live-build/setuphelfer-rescue-live/binary/live/filesystem.squashfs` (433655808 B)

## Inhalt

| Prüfpunkt | Ergebnis |
|-----------|----------|
| Squashfs vorhanden | **yes** |
| /opt/setuphelfer-rescue | **yes** |
| devserver_agent | **yes** |
| rescue_agent Modul | **no** (nicht erforderlich) |
| setuphelfer-qemu-smoke-autopilot.service | **yes** (Unit-Datei) |
| Autopilot enabled/wanted | **no** — kein Symlink in `etc/systemd/system/multi-user.target.wants/` |
| setuphelfer-dev-agent.service | **yes** (Unit-Datei) |
| Dev-Agent enabled/wanted | **no** (bewusst; Autopilot übernimmt) |
| Devserver-Endpunkt in Autopilot-Unit | **yes** (`http://10.0.2.2:8001`) |
| setuphelfer-qemu-smoke-autopilot.sh | **yes** (`usr/local/sbin/`) |

## Autopilot-Unit (Auszug)

```
Environment=SETUPHELFER_DEV_AGENT_SERVER_URL=http://10.0.2.2:8001
TTYPath=/dev/ttyS0
WantedBy=multi-user.target
```

Hook 090 (`systemctl enable setuphelfer-qemu-smoke-autopilot.service`) hat im Chroot **keinen** wants-Symlink hinterlassen — gleiche Lücke wie beim fehlgeschlagenen Standard-ISO-Smoke, trotz korrektem Profil/Bootappend.

## Status

**review_required** — Serial/Bootappend OK; Autostart-Gap für Autopilot-Unit offen.
