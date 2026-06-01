# QEMU Developer Smoke — Serial Visibility Retry

**Stand:** 2026-06-01
**HEAD:** `b6b842d`
**RUN_ID:** `qemu_rescue_developer_serial_20260601_160824`
**SESSION_ID:** `fleet-qemu_rescue_developer_serial_20260601_160824`
**Repository:** PUBLIC — **Push blocked**

## Ergebnis (Mindestziel nicht erreicht)

| Kriterium | Ergebnis |
|-----------|----------|
| `qemu-serial.log` existiert | **yes** |
| `serial_size_bytes` | **0** |
| `serial_non_empty` | **no** |
| `qemu_exit_code` (Autopilot) | **124** (timeout) |
| Diagnostic Export | **yes** — `serial_empty_boot_unknown` |
| Gast-Report / Ingest | **no** (`report_new=false`, `guest_found=false`) |

**Fehlerklasse:** `serial_empty_boot_unknown` (unverändert trotz neuer ISO `be016f2a…`).

**Nächster Prompt:** `FIX_QEMU_SERIAL_DEVICE_OR_BOOTLOADER_OUTPUT_CAPTURE`

## ISO

| Feld | Wert |
|------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| SHA256 | `be016f2adacfc9906b4b92ca8ab0d6b0390ad1e39a1e2cbb1f0a98eb35241a3f` (vor Lauf verifiziert) |

## QEMU-Lauf

| Feld | Wert |
|------|------|
| Gestartet | **yes** |
| KVM (Skript-Log) | **yes** (`-enable-kvm`, `/dev/kvm`) |
| Proxy | `0.0.0.0:8001` → `127.0.0.1:8000` (lab, Operator-Confirm) |
| Timeout | 1200 s |
| Wrapper Exit | 0 |
| QEMU CMD (Serial) | `-serial file:…/qemu-serial.log` |
| Display | `none` (headless autopilot) |

## Serial / Marker

| Marker / Inhalt | Sichtbar |
|-----------------|----------|
| Kernel/Boot-Text | **no** |
| systemd | **no** |
| `SETUPHELFER_BOOT_MARKER_START` | **no** |
| `SETUPHELFER_SYSTEMD_MARKER_START` | **no** |
| `SETUPHELFER_AUTOPILOT_START` | **no** |
| `SETUPHELFER_DEVSERVER_AGENT_START` | **no** |
| `SETUPHELFER_DEVSERVER_AGENT_REPORT_ATTEMPT` | **no** |

`qemu-gtk-stderr.log`: `terminating on signal 15 from pid … (timeout)`

## Diagnostic Export

| Feld | Wert |
|------|------|
| Export API | **yes** |
| `classification.primary` | `serial_empty_boot_unknown` |
| `serial_excerpt_head/tail` | leer |
| `secrets_detected` | false |
| Redaction | aktiv, keine Secrets |

## Devserver

| Feld | Vorher | Nachher |
|------|--------|---------|
| `reports_last_24h` | 0 | 0 |
| `report_new` | — | **false** |
| `node_count` | 2 | 2 (kein neuer Gast-Knoten) |
| Fake-VM | — | **no** (kein neuer Knoten) |

## Vergleich 081222

| | 081222 (alte ISO) | Dieser Lauf (neue ISO) |
|---|-------------------|------------------------|
| Serial bytes | 0 | 0 |
| Klasse | `serial_empty_boot_unknown` | gleich |
| ISO SHA | `6a44d1fe…` | `be016f2a…` |
| Cmdline tty0+debug | nein (quiet splash) | ja (statisch im ISO) |

**Schluss:** Serial-Leerstand ist **nicht** allein durch alte ISO-Cmdline erklärbar; QEMU-Serial-Capture oder Gast-Boot auf `ttyS0` muss separat gefixt werden.

## Guardrails

Kein ISO-Build, USB, Backup, Restore, apt, Push, kein zweiter QEMU-Lauf.

## Evidence-Pfad

`docs/evidence/runtime-results/rescue/qemu/qemu_rescue_developer_serial_20260601_160824/`
