# QEMU 143148 — Raw Review

**Run-ID:** `qemu_rescue_developer_autopilot_20260604_143148`

| Prüfung | Ergebnis |
|---------|----------|
| QEMU gestartet | **yes** |
| Autopilot-Status | `failed` (`qemu_exit_code` **124** timeout) |
| `guest_found` | **false** |
| `report_new` | **false** |
| Serial vorhanden | **yes** |
| Serial-Größe | **136229** B |
| Bootloader/ISOLINUX | **yes** |
| Kernel | **yes** |
| systemd/multi-user | **yes** (journald bis ~1200s) |
| Autopilot-Marker | **yes** |
| `ModuleNotFoundError` | **no** |
| `Invalid Host header` | **no** |
| `agent_send_failed` | **yes** |
| `SEND_HTTP_STATUS` | **yes** (`http_status=0`) |
| `SEND_RESPONSE_BODY` | **yes** |
| `SEND_OK` | **no** |
| `SEND_FAILED` | **yes** |

## Konkrete neue Ursache (Serial)

Gast-CLI scheitert vor HTTP:

```text
/opt/setuphelfer-rescue/backend/venv/bin/python3: GLIBC_2.38 not found
```

Host-Health über Proxy: **ok** (`host_health_ok=true`, Dev-Server `local_lab` enabled).

Autopilot-Script und Serial-Marker aus `ddd502e` sind im ISO aktiv; Blocker ist **Gast-Python/venv vs. Live-GLIBC**, nicht Import/Host-Header/Profil-Preflight.
