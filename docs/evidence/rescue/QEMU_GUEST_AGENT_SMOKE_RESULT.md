# QEMU Guest Agent Smoke — Ergebnis

**Stand:** 2026-06-02  
**HEAD:** `c70bfe1`  
**Status:** **`blocked`**

## Zusammenfassung

| Feld | Wert |
|------|------|
| QEMU gestartet | **no** |
| Blocker | `qemu_smoke_blocked_by_profile` — `sudo` für `local_lab` im Agent-Kontext nicht verfügbar |
| ISO-Fingerprint | **ok** |
| Tooling/KVM | **ok** |
| release nach Lauf | **unchanged** (`release`, gate green) |

## Guardrails eingehalten

Kein ISO-Build, kein lb build, kein QEMU, kein USB/dd, kein Host-Disk-Attach, kein Backup/Restore.

## Squashfs-Risiken (vor Smoke bestätigt)

- `devserver_agent` vorhanden; `rescue_agent/` fehlt im Bundle
- `setuphelfer-dev-agent.service` vorhanden, **nicht** in `multi-user.target.wants`

## Operator-Fortsetzung

Im Operator-Terminal (mit `sudo -v`):

```bash
cd /home/volker/piinstaller
sudo -v
./scripts/rescue-live/qemu-guest-agent-smoke-operator.sh
```

Skript: `local_lab` → QEMU-Autopilot (1200s, kein Host-Disk) → Fleet/Dev-Server-Ingest → **release-Trap**.

JSON: `qemu_guest_agent_smoke_latest.json`

## Nächster Schritt

Operator-QEMU-Smoke ausführen; danach Evidence-Ingest erneut auswerten.

Rescue-Stick bleibt **nicht vollständig grün** ohne Boot-/Agent-/USB-Nachweis.
