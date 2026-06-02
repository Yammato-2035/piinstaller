# QEMU Guest Agent Smoke — Failure Classification

**Run-ID:** `qemu_rescue_developer_autopilot_20260602_202725`  
**Datum:** 2026-06-02

## root_cause_classification

**`qemu_serial_capture_failure`**

Mit wesentlichem Mitursache-Faktor **`guest_agent_autostart_gap`** (Profil/Enable).

## Begründung

### 1. Serial leer (Primärbeleg)

- `qemu-serial.log`: **0 Bytes** über 1200s
- QEMU Exit **124** (Timeout)
- Fleet-Session: `serial_empty`, `guest_report_missing`
- ISO bootappend (Standard): `quiet splash` — **ohne** `console=ttyS0`
- Autopilot-Parser: `guest_smoke_from_serial: null` → `guest_found=false`

### 2. Autostart-Gap (Mitursache)

- `setuphelfer-qemu-smoke-autopilot.service` im Squashfs, **nicht** in `multi-user.target.wants`
- `setuphelfer-dev-agent.service` ebenfalls **nicht** enabled
- Standard-Profil-Build aktiviert diese Units nicht (`prepare-controlled-live-build-tree.sh` nur für `developer`/`developer-qemu`)

### 3. Kein Netzwerk-/Proxy-Fehler belegt

- Proxy lief: `0.0.0.0:8001` → `127.0.0.1:8000`
- `local_lab` war aktiv während Smoke
- Kein Agent-Lauf nachweisbar → Devserver-Erreichbarkeit **nicht getestet**

## Ausgeschlossen

| Hypothese | Grund |
|-----------|-------|
| qemu_boot_failure (Kernel-Panic) | Nicht belegbar — Serial leer |
| guest_devserver_network_gap | Agent nicht gestartet, kein Netzwerkversuch in Logs |
| guest_agent_bundle_gap (devserver) | `devserver_agent/` vorhanden |
| USB/Host-Disk/Restore | Guardrails eingehalten (operator log) |
| Fake-Green | `guest_found=false`, `report_new=false` korrekt |

## Offen

- Ob Gast trotz leerem Serial gebootet hat (Framebuffer `-display none` → unbeobachtet)
- Ob `rescue_agent/`-Modul fehlt relevant wäre (Smoke nutzt `devserver_agent`)

## Warum kein Fake-Green

Kein Bootmarker, kein Agent-Marker, kein Report, Fleet final `timeout`/`guest_report_missing`.

## Nächster Schritt

1. **ISO mit `developer-qemu`-Profil** rebuilden (Serial + Autopilot-Enable), **oder**
2. Standard-ISO bootappend um `console=ttyS0` ergänzen **und** Autopilot-Unit enablen
3. Erst danach erneuter QEMU-Autopilot-Smoke (separater Operator-Lauf)

Empfohlene Aktion: `qemu_serial_console_fix_or_rebuild_developer_qemu_profile` + `fix_guest_agent_systemd_enable`
