# KB — Rescue/QEMU wiederkehrende Fehler

## `agent_send_failed` — Historie

| Phase | Ursache | Fix-Versuch | Evidence |
|-------|---------|-------------|----------|
| 212528 (vor Payload-Fix) | `ModuleNotFoundError` devserver_agent | PYTHONPATH + `-m devserver_agent.cli` | `886a098` |
| 212528 (nach Import-Fix) | `Invalid Host header` | Lab Host header `127.0.0.1:8000` | `886a098` |
| 212528 (nach Host-Fix) | `dev_server_disabled` / Profil-Desync / Token | `ddd502e` profile sync + require_token=false | `QEMU_GUEST_REPORT_PAYLOAD_*` |
| 143148 (aktuell) | **`GLIBC_2.38 not found`** Gast-venv | **offen** — kein erneuter Import/Host-Fix | `QEMU_143148_FAILURE_CLASSIFICATION.md` |

## Aktueller Blocker (143148)

```text
/opt/setuphelfer-rescue/backend/venv/bin/python3: GLIBC_2.38 not found
```

**Klassifikation:** `guest_rescue_venv_glibc_mismatch`  
**Nicht wiederholen:** Import-Pfad-, Host-Header-, Profil-only-Fixes ohne venv/GLIBC-Anpassung.

**Nächste Richtung:** system-`python3` im Live-Image oder im Chroot gebautes venv für Rescue-Bundle; Clean → Prepare → Build → Squashfs-Validate → QEMU.

## `guest_found=false` / Serial-Parser

- Einzeiliges JSON mit systemd-ANSI → Multi-Line BEGIN/END (`ddd502e`).
- Prüfen: Parser + Serial-Marker `SETUPHELFER_DEVSERVER_AGENT_SEND_*`.

## stale ISO / Squashfs

**Klassifikation:** `known_error_fix_not_in_artifact`

Pflichtkette: Clean → Prepare → validate_tree=0 → Build → validate_iso → QEMU.

Evidence: `PAYLOAD_FIX_REBUILD_QEMU_RESULT.md`, `payload_fix_rebuild_qemu_latest.json`

## USB

Gesperrt bis `guest_report_received=true` nach erfolgreichem QEMU-Ingest.
