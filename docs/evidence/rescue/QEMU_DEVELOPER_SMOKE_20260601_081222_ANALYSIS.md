# QEMU Developer Smoke — Analyse Lauf `081222`

**Stand:** 2026-06-01  
**Modus:** STRICT — nur Evidence-Auswertung, kein neuer QEMU-Lauf, kein ISO-Build.

## Identifikation

| Feld | Wert |
|------|------|
| **RUN_ID** | `qemu_rescue_developer_autopilot_20260601_081222` |
| **SESSION_ID** | `fleet-qemu_rescue_developer_autopilot_20260601_081222` |
| **Git HEAD (Analyse)** | `3af6f06` (Fleet Wrapper JSON-Fix) |
| **Evidence-Verzeichnis** | `docs/evidence/runtime-results/rescue/qemu/qemu_rescue_developer_autopilot_20260601_081222/` |

## Kurzfazit

| Frage | Antwort (Evidence) |
|-------|-------------------|
| Bootet die ISO überhaupt? | **Unbekannt** — keine Kernel-/Bootloader-Zeile auf Serial |
| Gibt es Serial-Ausgabe? | **Nein** — `qemu-serial.log` = **0 Bytes** nach vollem Lauf |
| Startet systemd? | **Nicht nachweisbar** (Serial leer) |
| Startet der Autopilot? | **Nicht nachweisbar** — erwartete Zeile `SETUPHELFER_AUTOPILOT_START` fehlt |
| Erreicht Gast `10.0.2.2:8001`? | **Nicht nachweisbar** |
| Devserver-Agent im Gast gefunden? | **Nein** (weder Serial noch Ingest) |
| Report erzeugt, Ingest fehlgeschlagen? | **Nein** — kein neuer Report/Knoten |
| Gast bis Anwendung gekommen? | **Unbekannt / unwahrscheinlich** — Timeout 1200s, kein Signal auf Serial oder Dev-Server |

**Hauptfehlerklasse:** `serial_empty_boot_unknown` (primär) + `qemu_wrapper_ok_guest_no_report` (sekundär).

**Nächster gezielter Prompt (ohne QEMU-Retry):** `FIX_RESCUE_ISO_SERIAL_CONSOLE_AND_BOOT_VISIBILITY`

## QEMU / Host

| Merkmal | Wert |
|---------|------|
| KVM | **Ja** — Skript loggt „QEMU: KVM enabled“; `-enable-kvm -cpu host` |
| Timeout | 1200 s |
| Headless | Ja (`-display none`) |
| **qemu_exit_code** | **124** (`timeout` beendet QEMU, Signal 15) |
| Serial-Device | `-serial file:…/qemu-serial.log` (Wrapper korrekt) |
| Proxy | `GUESTFWD_PROXY=true`, `HOST_DEV_URL=http://10.0.2.2:8001`, Bind `0.0.0.0:8001` → `127.0.0.1:8000` (lab-only, NDA gelb) |

`qemu-gtk-stderr.log`:

```
qemu-system-x86_64: terminating on signal 15 from pid … (timeout)
```

## Autopilot-Result (`qemu_autopilot_result.json`)

| Feld | Wert |
|------|------|
| status | `failed` |
| autopilot | true |
| qemu_exit_code | 124 |
| host_dev_server_url | `http://10.0.2.2:8001` |
| lab_proxy_enabled | true |
| guest_smoke_from_serial | `null` |
| dev_server_reports_before / after | 0 / 0 |
| dev_server_report_new | false |

**Hinweis:** `report_new` / `guest_found` stammen aus dem Wrapper-Stdout (Python-Summary am Ende des Skripts), nicht als eigene JSON-Felder in der Datei. Ableitung: `report_new=false`, `guest_found=false` (kein Serial-Parse, kein Report-Delta).

**autopilot_result_incomplete:** Felder `serial_size`, `serial_path`, `duration`, `errors`, `warnings`, `evidence_paths` fehlen in der JSON-Datei (nur Kernfelder geschrieben).

**Status `failed`:** weil `qemu_exit_code==124` und kein `guest` aus Serial → Skript-Logik `failed` (nicht `review_required`).

## Serial (`qemu-serial.log`)

| Merkmal | Wert |
|---------|------|
| Vorhanden | ja |
| **Größe** | **0 Bytes** (auch nach 1200s Lauf) |
| **Klassifikation** | `serial_empty_after_qemu_run` |

**Gegenprobe ISO-Strings:** In `binary.hybrid.iso` ist `console=ttyS0,115200n8` in mehreren `append`-Zeilen sichtbar (`strings`); dennoch keine Host-Datei-Ausgabe.

**Mögliche Ursachen (nicht einzeln belegbar ohne Serial):**

- ISO bootet nicht / hängt vor Kernel-Konsole
- Kernel schreibt nur auf `tty0` / `quiet splash` unterdrückt frühe Ausgabe
- Live-System erreicht `multi-user.target` nicht
- Autopilot-Unit startet nicht
- QEMU-Serial-Anbindung (unwahrscheinlich — Standard `file:`-Backend)

**Autopilot erwartet auf Serial:** `SETUPHELFER_AUTOPILOT_START run_id=…` (`setuphelfer-qemu-smoke-autopilot.sh`) — **nicht vorhanden**.

## Development Server / Ingest

| Prüfung | Ergebnis |
|---------|----------|
| `dev_server_summary_before` vs `after` | identisch: `node_count=2`, `reports_last_24h=0` |
| Neuer Knoten | **nein** (weiterhin `agent-smoke-node`, `local-smoke-node`) |
| Neue Reports zum Run | **nein** |
| `dev_server_reports_after.json` | 2 historische Reports (Mai 2025-30), keine `081222`-Referenz |

**Rescue Guest Report Ingest:** **rot** für diesen Lauf — kein Gast-Report.

## ISO (read-only, kein Build)

| Merkmal | Wert |
|---------|------|
| Pfad | `build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso` |
| Größe | 488 MiB |
| mtime | 2026-06-01 ~07:54 (vor Lauf 08:12) |
| Boot append (ISO) | `console=ttyS0,115200n8 quiet splash` + live-Parameter |
| Workspace prepare | `console=tty0 console=ttyS0,115200n8` (ohne `quiet splash` in `prepare-controlled-live-build-tree.sh`) |

**Profil:** `developer-qemu` — Autopilot-Unit + Skript im Repo-Profil; Gast-Pfad `/opt/setuphelfer-rescue`, Agent-URL `http://10.0.2.2:8001`.

## Abgrenzung Lauf `080405`

Lauf `qemu_rescue_developer_autopilot_20260601_080405` wird **nicht** als Boot-Failure für `081222` gewertet. Dort dominierte der Fleet-JSON-Wrapper-Bug (`exists=true` in Python); `081222` lief **nach** Fix `3af6f06` mit sauberer Wrapper-Telemetrie-Erstellung, scheiterte aber weiterhin an leerem Serial + fehlendem Gast-Report.

## Fleet Session (Kurzverweis)

Siehe `docs/evidence/dev-dashboard/FLEET_SESSION_QEMU_RUN_20260601_081222_ANALYSIS.md`.

- Session endet `timeout`, `finished_at` gesetzt.
- `qemu.exit_code` in API/latest: **null** (Finish-Payload mit Exit 124 nicht in persisted Session sichtbar).
- Heartbeats: `last_heartbeat_at` = Erstellzeit — **keine** erfolgreichen Heartbeat-Updates während QEMU (~1263 s stale → `timeout` via `_apply_stale_rules` beim GET).

## Fehlerklassen-Matrix (Lauf 081222)

| Klasse | Zutreffend | Evidence | Gegenbeleg |
|--------|------------|----------|------------|
| 1 `qemu_wrapper_ok_guest_no_report` | **ja** | Exit 124, Proxy konfiguriert, Fleet-Session angelegt, kein Report | — |
| 2 `serial_empty_boot_unknown` | **ja (primär)** | 0 B Serial, 1200s | ISO-String hat ttyS0 |
| 3 `iso_boots_agent_not_started` | nicht belegbar | — | Serial leer |
| 4 `agent_started_network_failed` | nicht belegbar | — | — |
| 5 `agent_started_ingest_failed` | nein | kein Report | kein Agent-Nachweis |
| 6 `module_path_error_devserver_agent` | nicht belegbar | — | — |
| 7 `systemd_init_missing_or_failed` | nicht belegbar | — | — |
| 8 `iso_artifact_outdated_or_wrong_profile` | gelb | ISO frisch, Profil im Tree; Serial trotz ttyS0 leer | mtime vor Lauf |
| 9 `fleet_finish_missing` | **teilweise** | `finished_at` ja; `exit_code`/Finish-Findings fehlen | Status `timeout` vorhanden |
| 10 `inconclusive_evidence_missing` | nein | ausreichend für Serial+Ingest-Klasse | — |

## Guardrails (eingehalten)

- Kein neuer QEMU-Lauf
- Kein ISO-Build / USB / Backup / Restore / apt
- Kein Public Push
- Keine Fake-VM

## Artefakte

- `qemu_autopilot_result.json`
- `qemu-serial.log` (0 B)
- `qemu-gtk-stderr.log`
- `dev_server_summary_{before,after}.json`
- `dev_server_reports_after.json`
- `qemu_gtk_pid.txt`
