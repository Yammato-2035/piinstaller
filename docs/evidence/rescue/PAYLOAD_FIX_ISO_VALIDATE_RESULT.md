# Payload Fix — ISO Validate

**Status:** `ready_for_qemu_guest_report_smoke`

| Feld | Wert |
|------|------|
| ISO SHA256 | `1899f5cabf9d40c9581805def9a765557a2168fc11ac181b0f71bfc0b1ff0691` |
| `validate_iso_exit` | **0** |
| developer-qemu | **yes** |
| Autopilot-Wants | **yes** |
| `SETUPHELFER_DEVSERVER_AGENT_SEND_*` | **yes** (9 Marker im Squashfs-Autopilot) |
| Host-Header-Fix (Autopilot) | **yes** |
| Backend-Profil-Sync | **yes** (deployed `/opt`) |

**Hinweis:** Squashfs-Bundle `devserver_agent/client.py` noch Stand 2026-05-30; Gast-Agent nutzt primär **venv-Python** → GLIBC-Mismatch (siehe QEMU).
