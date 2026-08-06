# Hardware-Baseline-Diagnostik — Rescue Stick

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 14).

Sprachen: [Deutsch](HARDWARE_BASELINE_DIAGNOSTICS_DE.md) ·
[English](HARDWARE_BASELINE_DIAGNOSTICS_EN.md) ·
[Français](HARDWARE_BASELINE_DIAGNOSTICS_FR.md) ·
[Nederlands](HARDWARE_BASELINE_DIAGNOSTICS_NL.md)

Verwandt: [Hardware Compatibility Model (DE)](HARDWARE_COMPATIBILITY_MODEL_DE.md).

> Übersetzungshinweis: Diese Fassung ist strukturell vollständig und inhaltlich
> abgestimmt. Eine native sprachliche Endredaktion kann noch ausstehen.

## 1. Zweck der frühen Hardware-Baseline

Die frühe Hardware-Baseline ist ein **kurzer, sicherer Risikocheck** beim Start
des Rettungssystems. Sie prüft Arbeitsspeicher, CPU, GPU und Massenspeicher auf
Hinweise für akute Probleme — bevor Backup, Restore, OS-Installation oder GUI
genutzt werden.

Sie ersetzt weder Memtest86+, noch SMART-Selbsttests, noch Stress-Benchmarks.
Vertragliche Grundlage: `backend/core/hardware_baseline_contracts.py`.
Orchestrierung: `backend/rescue/hardware_baseline_orchestrator.py`.

## 2. Ampelfarben und BaselineStatus-Vokabular

| Ampel (`BaselineSeverity`) | Typische Statuswerte (`BaselineStatus`) |
|---|---|
| 🟢 `green` | `no_immediate_issue_detected` |
| 🟡 `yellow` | `degraded`, `review_required`, `extended_test_recommended` |
| 🔴 `red` | `immediate_issue_detected`, `extended_test_required` |
| ⚪ `gray` | `test_unavailable`, `not_tested` |

Bedeutung der Statuswerte:

| Status | Bedeutung |
|---|---|
| `no_immediate_issue_detected` | Kein akuter Hinweis in den Schnellchecks; **keine** Fehlerfreiheitsgarantie |
| `immediate_issue_detected` | Akuter Befund (z. B. MCE, kritische SMART-/NVMe-Warnung, Kernel-GPU-Hang) |
| `degraded` | Eingeschränkter Zustand, Betrieb möglich aber auffällig |
| `review_required` | Operatorprüfung nötig (unklare oder widersprüchliche Daten) |
| `extended_test_recommended` | Längerer Test empfohlen, nicht automatisch gestartet |
| `extended_test_required` | Längerer Test fachlich erforderlich vor kritischen Schreibaktionen |
| `test_unavailable` | Werkzeug/Sensor fehlt; Check übersprungen, nicht „bestanden“ |
| `not_tested` | Subsystem noch nicht geprüft |

Es gibt **kein** Statuswort wie `healthy`, `ok` oder `passed`. Verbotene
Aussagen sind in `FORBIDDEN_BASELINE_CLAIMS` definiert.

## 3. Arbeitsspeicher-Baseline (`memory_baseline_diagnostics.py`)

Additive Checks:

1. **Inventur** — `/proc/meminfo`, optional `dmidecode -t memory`
2. **Kernel-/HW-Fehler** — EDAC / MCE / OOM-Signale aus `dmesg`
3. **Plausibilität** — physisch gemeldet vs. kernel-nutzbar
4. **Quick Probe** — begrenzter In-Process-Puffer, maximal **128 MiB** bzw.
   **2 % von `MemAvailable`** (je nachdem, was kleiner ist); nie ein voller
   Memtest, nie Installation von `memtester` / `stress-ng` / `rasdaemon`

## 4. CPU-Baseline (`cpu_baseline_diagnostics.py`)

Baut auf `cpu_platform_detection` auf und ergänzt:

- MCE / Hardware-Error / Lockup / Watchdog-Scan (`dmesg`)
- thermische Temperaturen und Throttling-Hinweise (`sysfs`)
- begrenzter, deterministischer Quick Probe

**Nie** `stress-ng`, Prime95 oder ähnliche Dauerlast. Kein Microcode-/BIOS-Update.

## 5. GPU-Baseline (`gpu_baseline_diagnostics.py`)

Wiederverwendet `gpu_detection.build_gpu_report` als einzige Inventurquelle und
ergänzt:

- Render-Nodes (`/dev/dri/renderD*`)
- Kernel-/Firmware-Fehler (Hang, Reset, Fence-Timeout, Xid)
- optionale Lese-Probes: `glxinfo` / `eglinfo` / `vulkaninfo`

Fehlende Treiber/Firmware → typisch `yellow`/`review_required`. Kritische
Kernel-GPU-Fehler → `red`. Kein Treiber-Install, kein Modprobe-/Cmdline-Schreiben.

## 6. HDD / SATA-SSD / NVMe-Baseline

Gemeinsame Schicht: `storage_baseline_diagnostics.py` (Kernel-I/O-Fehler,
Tool-Verfügbarkeit). Geräteklassen:

| Klasse | Modul | Typische Quellen |
|---|---|---|
| HDD | `hdd_baseline_diagnostics.py` | `smartctl` Attribute (u. a. 5/197/198/199/194) |
| SATA-SSD | `sata_ssd_baseline_diagnostics.py` | Wear/Spare/Uncorrectable/CRC, TRIM |
| NVMe | `nvme_baseline_diagnostics.py` | `nvme smart-log` / `nvme id-ctrl` |

Es werden **nur vorhandene** SMART-/NVMe-Attribute gelesen. Ein SMART-Self-Test
(`smartctl -t`, erweiterte NVMe-Self-Tests) wird **niemals automatisch** gestartet.

## 7. Grenzen der Schnelltests

- 🟢 `green` / `no_immediate_issue_detected` bedeutet **nicht**, dass Hardware
  fehlerfrei oder langfristig stabil ist.
- Ein Quick Probe deckt nur einen winzigen Speicher-/CPU-Ausschnitt ab.
- Fehlende Tools liefern `test_unavailable` / `gray`, nicht „alles gut“.
- Erweiterte Tests (Memtest86+, SMART self-test, GPU-Render-Stress) liegen
  außerhalb dieses Schnellpfads.

## 8. `HardwareBaselineGate`

Implementierung: `backend/rescue/hardware_baseline_gate.py`.

Felder (additiv zu `core.safety_facade`, **niemals** als Bypass):

| Feld | Rolle |
|---|---|
| `backup_allowed` | Lesendes Notfall-Backup bleibt grundsätzlich möglich |
| `restore_allowed` | Restore nur ohne rote data-critical-Befunde und nach vollständiger Prüfung |
| `os_installation_allowed` | OS-Installation analog zu Restore |
| `gui_mode_allowed` | GUI nur ohne roten GPU-Befund |

Beide Schichten müssen zustimmen: Baseline-Gate **und** `safety_facade`.

## 9. Auswirkungen kritischer Befunde

| Befund | Wirkung |
|---|---|
| Rot bei Memory / CPU / Storage (aggregiert) | blockiert Restore und OS-Installation |
| Rot bei GPU | blockiert GUI (`gui_mode_allowed=false`), **nicht** Backup |
| Rote **Quell**-Platte | bleibt backupfähig (Lesen ist der Sinn des Notfall-Backups) |
| Rote **Ziel**-Platte | niemals beschreibbar für Backup-Ziel, Restore oder OS-Installation |

Auswertung pro Operation: `evaluate_operation_against_baseline_gate`.

## 10. API-Routen (read-only / bounded)

Modul: `backend/api/routes/rescue_hardware_baseline.py`.

| Methode | Pfad | Zweck |
|---|---|---|
| `GET` | `/api/rescue/hardware/baseline/status` | Gate-/Laufstatus oder `{has_run:false}` |
| `POST` | `/api/rescue/hardware/baseline/quick` | Schnell-Baseline starten |
| `POST` | `/api/rescue/hardware/baseline/extended-preview` | gleiche Checks, Empfehlungen betont |
| `GET` | `/api/rescue/hardware/baseline/latest` | letzter Gesamtlauf |
| `GET` | `/api/rescue/hardware/baseline/memory` | Memory-Subsystem |
| `GET` | `/api/rescue/hardware/baseline/cpu` | CPU-Subsystem |
| `GET` | `/api/rescue/hardware/baseline/gpu` | GPU-Subsystem |
| `GET` | `/api/rescue/hardware/baseline/storage` | alle Storage-Ergebnisse |
| `GET` | `/api/rescue/hardware/baseline/storage/{device_id}` | ein Gerät |

Keine Route startet Installationen, Firmware-Updates, Formatierungen oder
SMART-Self-Tests.

## 11. Erweiterte Tests benötigen Operatorbestätigung

`ExtendedTestRecommendation.operator_confirmation_required` ist standardmäßig
`true`. `/extended-preview` liefert nur Empfehlungen (`memtest86plus`,
`cpu_stress`, `gpu_render_stress`, `smart_self_test_short`, …) und startet
keinen Langzeittest. Jeder erweiterte Test erfordert eine **explizite,
getrennte Operatoraktion** außerhalb dieser API.

## 12. Datenschutz

Baseline-Telemetrie folgt `telemetry_redaction_contract.py` /
`hardware_dcc_status.py`: **keine Seriennummern, keine MAC-Adressen, keine
IP-Adressen** in Telemetrie-Payloads. Device-IDs bleiben technische
Blockgerätnamen (z. B. `sda`, `nvme0n1`), keine Hardware-Serien.
