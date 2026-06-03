# QEMU Guest Report Payload — Fix Decision

**Gewählter Fall:** **B + D** (Payload/Runtime + Lab-Token/Enable)

## Konkrete Ursache

1. **`local_lab`-Profil** registriert Dev-Server-Router, aber **`load_dev_server_config()`** lieferte `enabled=false`** → `validate_server_health` → `dev_server_disabled` → CLI Exit ≠ 0.
2. **`post_report`** ohne **`Host: 127.0.0.1:8000`** über QEMU-Proxy (nur Health-curl im Autopilot hatte Override).
3. **`require_token=true`** default ohne konfiguriertes Lab-Token → ingest blockiert.
4. Serial-JSON **korrupt** (systemd-ANSI) → Host `guest_found=false` unabhängig vom HTTP-Ergebnis.

## Codeänderungen

| Bereich | Fix |
|---------|-----|
| `backend/devserver/config.py` | Profil-Sync: `local_lab` → enabled + mode + `require_token=false` |
| `packaging/.../92-install-profile-local-lab.conf.example` | Explizite Dev-Server-Env |
| `backend/devserver_agent/client.py` | Auto `Host: 127.0.0.1:8000` für `10.0.2.2` URLs |
| `backend/devserver_agent/cli.py` | `--print-payload`, `--dry-run` |
| Autopilot + Parser | Serial HTTP-Marker + Multi-Line JSON |
| Validator | `devserver_agent.cli` subprocess-tolerant |

## USB

**Gesperrt** bis QEMU `guest_report_received=true` nach ISO-Rebuild + Deploy.

Port-/Profilfehler waren **nicht** Primärursache (Preflight ok).
