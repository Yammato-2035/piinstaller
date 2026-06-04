# Payload Fix — ISO Validate

**Status:** `review_required` (bestehendes ISO, nicht nach `ddd502e` Rebuild)

| Feld | Wert |
|------|------|
| ISO | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` (stale, ~488 MB, 2026-06-03 23:25) |
| `validate_iso_exit` (Validator-Skript) | **0** auf bestehendem ISO |
| `SETUPHELFER_DEVSERVER_AGENT_SEND_*` im Squashfs | **no** — Squashfs `client.py` vom 2026-05-31, Autopilot ohne Serial-HTTP-Marker |
| Host-Header-Fix im Gast | **no** (bis Rebuild) |
| Backend-Profil-Sync | **teilweise** in `/opt` (manueller Sync) |

**Nicht** `ready_for_qemu_guest_report_smoke` — ISO-Inhalt entspricht nicht Commit `ddd502e`.
