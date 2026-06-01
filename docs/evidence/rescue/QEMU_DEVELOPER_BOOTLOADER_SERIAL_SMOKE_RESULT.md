# QEMU Developer Bootloader Serial Smoke — Result

**Stand:** 2026-06-01
**HEAD:** `727df3c`
**Branch:** `main`
**Repository:** PUBLIC — **Push blocked**
**ISO SHA256:** `5c79e35c35a227bdcb9978c1728d8d6aaeef515938ce13358ca6b994d293829a`

## Run

| Feld | Wert |
|------|------|
| RUN_ID | `qemu_rescue_developer_bootserial_20260601_202000` |
| SESSION_ID | `fleet-qemu_rescue_developer_bootserial_20260601_202000` |
| local_lab aktiviert | **no** (Agent: sudo Passwort; Runtime blieb `release`) |
| QEMU gestartet | **yes** |
| KVM enabled | **yes** |
| proxy bind | `0.0.0.0:8001` → `127.0.0.1:8000` |
| Wrapper exit | **0** |
| qemu_exit_code | **124** (timeout 1200s) |
| Autopilot status | **failed** |
| report_new | **false** |
| guest_found | **false** |

## Serial (Mindest-Erfolg)

| Feld | Wert |
|------|------|
| serial_log_exists | **yes** |
| serial_size_bytes | **132412** |
| serial_non_empty | **yes** |
| Pfad | `docs/evidence/runtime-results/rescue/qemu/qemu_rescue_developer_bootserial_20260601_202000/qemu-serial.log` |

### Wichtigste Funde

- **ISOLINUX** 6.04 — `Loading /live/vmlinuz... ok`
- **Linux** 6.1.0-49-amd64 — Cmdline mit `console=tty0` + `console=ttyS0,115200n8`
- **systemd** 252 — `Reached target` (network, basic, getty)
- **Setuphelfer-Units** registriert: `setuphelfer-qemu-smoke-autopilot`, `setuphelfer-serial-boot-markers`, `setuphelfer-dev-agent`
- **Keine** `SETUPHELFER_AUTOPILOT_START` / Agent-Marker in Serial (Timeout; Host-Dev-API 404 in release)

### Serial-Auszug (Head)

```
ISOLINUX 6.04 20240408  Copyright (C) 1994-2015 H. Peter Anvin et al
Loading /live/vmlinuz... ok
Loading /live/initrd.img...ok
[    0.000000] Linux version 6.1.0-49-amd64 ...
[    0.000000] Command line: ... console=tty0 console=ttyS0,115200n8 loglevel=7 ...
```

## Marker-Sichtbarkeit

| Marker | Serial |
|--------|--------|
| Bootloader/ISOLINUX | **yes** |
| Linux version | **yes** |
| systemd | **yes** |
| SETUPHELFER_BOOT_MARKER_START | **no** |
| SETUPHELFER_AUTOPILOT_START | **no** |
| SETUPHELFER_DEVSERVER_AGENT_START | **no** |

## Diagnostic Export

| Feld | Wert |
|------|------|
| API verfügbar | **no** — HTTP **404** (`install_profile=release`) |
| classification.primary | *(nicht via API)* — manuell: **`bootloader_serial_visible`** |
| serial excerpt in Evidence | **yes** (diese Datei) |

**Hinweis:** Für API-Export `local_lab` vor Export aktivieren und `GET /api/dev-diagnostics/qemu-smokes/{RUN_ID}/export` erneut aufrufen.

## Fehlerklasse

**`bootloader_serial_visible`** — Serial-Capture-Fix wirkt; früheres `serial_empty_boot_unknown` behoben. Folge: Autopilot/Gast-Report (release-Runtime ohne Dev-Server-Routen, Timeout 124).

## Guardrails

Kein ISO-Build, kein USB/dd, kein Backup/Restore, kein apt, kein Push, genau ein QEMU-Lauf.

## Nächster Schritt

`ANALYZE_QEMU_AUTOPILOT_AND_DEVSERVER_AFTER_SERIAL_CAPTURE` — local_lab aktivieren, Autopilot-Marker und Devserver-Ingest prüfen (kein zweiter Blind-QEMU-Retry ohne Analyse).
