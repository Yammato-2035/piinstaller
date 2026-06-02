# QEMU Guest Agent Smoke — Risk Review (Squashfs)

**Datum:** 2026-06-02  
**Squashfs:** `binary/live/filesystem.squashfs`

| Risiko | Bestätigt |
|--------|-----------|
| `devserver_agent/` vorhanden | **yes** |
| `rescue_agent/` Modul | **no** → `rescue_agent_module_gap_confirmed` |
| `setuphelfer-dev-agent.service` | **yes** |
| Service in multi-user.target.wants | **no** → `autostart_gap_confirmed` |
| Backend/UI enabled | **yes** |

Dev-Agent-Unit (Auszug):
- `Environment=PYTHONPATH=/opt/setuphelfer-rescue`
- `ExecStart=... backend.devserver_agent.cli --send --json --qemu-host-fallback`
- `WantedBy=multi-user.target` (Datei vorhanden, **nicht** enabled)

## Bewertung

Bekannte Gaps **bestätigt** vor QEMU. Autostart des Dev-Agents im Live-System ist **nicht** durch enable-Wants abgedeckt — Autopilot-Unit (`setuphelfer-qemu-smoke-autopilot`) nur im `developer-qemu`-Profil, nicht in `standard`-Build.

Kein manuelles Nachstarten als Erfolg gewertet.
