# Hardware-baseline-diagnostiek — Rescue Stick

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 14).

Talen: [Deutsch](HARDWARE_BASELINE_DIAGNOSTICS_DE.md) ·
[English](HARDWARE_BASELINE_DIAGNOSTICS_EN.md) ·
[Français](HARDWARE_BASELINE_DIAGNOSTICS_FR.md) ·
[Nederlands](HARDWARE_BASELINE_DIAGNOSTICS_NL.md)

Zie ook: [Hardware Compatibility Model (NL)](HARDWARE_COMPATIBILITY_MODEL_NL.md).

> Vertaalnotitie: deze editie is structureel volledig en inhoudelijk
> afgestemd. Een native taalkundige eindredactie kan nog openstaan.

## 1. Doel van de vroege hardware-baseline

De vroege hardware-baseline is een **korte, veilige risicocheck** bij het
opstarten van het reddingssysteem. Zij scant geheugen, CPU, GPU en
massastorage op signalen van acute problemen — vóór backup, restore,
OS-installatie of GUI-gebruik.

Zij vervangt geen Memtest86+, SMART-selftests of stress-benchmarks.
Contractlaag: `backend/core/hardware_baseline_contracts.py`.
Orkestratie: `backend/rescue/hardware_baseline_orchestrator.py`.

## 2. Stoplichtkleuren en BaselineStatus-vocabulaire

| Licht (`BaselineSeverity`) | Typische statuswaarden (`BaselineStatus`) |
|---|---|
| 🟢 `green` | `no_immediate_issue_detected` |
| 🟡 `yellow` | `degraded`, `review_required`, `extended_test_recommended` |
| 🔴 `red` | `immediate_issue_detected`, `extended_test_required` |
| ⚪ `gray` | `test_unavailable`, `not_tested` |

Betekenis van de statuswaarden:

| Status | Betekenis |
|---|---|
| `no_immediate_issue_detected` | Geen acuut signaal in de snelle checks; **geen** foutvrijheidsgarantie |
| `immediate_issue_detected` | Acuut bevinding (bijv. MCE, kritieke SMART-/NVMe-waarschuwing, kernel-GPU-hang) |
| `degraded` | Beperkte toestand; bedrijf mogelijk maar opvallend |
| `review_required` | Operatorbeoordeling nodig (onduidelijke of conflicterende data) |
| `extended_test_recommended` | Langere test aanbevolen; nooit automatisch gestart |
| `extended_test_required` | Langere test vereist vóór kritieke schrijfacties |
| `test_unavailable` | Tool/sensor ontbreekt; check overgeslagen, niet „geslaagd” |
| `not_tested` | Subsystem nog niet onderzocht |

Er bestaat **geen** statuswoord zoals `healthy`, `ok` of `passed`. Verboden
beweringen staan in `FORBIDDEN_BASELINE_CLAIMS`.

## 3. Geheugen-baseline (`memory_baseline_diagnostics.py`)

Additieve checks:

1. **Inventaris** — `/proc/meminfo`, optioneel `dmidecode -t memory`
2. **Kernel-/HW-fouten** — EDAC- / MCE- / OOM-signalen uit `dmesg`
3. **Plausibiliteit** — fysiek gemeld vs. kernel-bruikbaar
4. **Quick probe** — begrensde in-process-buffer, maximaal **128 MiB** of
   **2 % van `MemAvailable`** (wat kleiner is); nooit een volledige Memtest,
   nooit installatie van `memtester` / `stress-ng` / `rasdaemon`

## 4. CPU-baseline (`cpu_baseline_diagnostics.py`)

Bouwt voort op `cpu_platform_detection` en voegt toe:

- MCE- / hardware-error- / lockup- / watchdog-scan (`dmesg`)
- thermische temperaturen en throttling-aanwijzingen (`sysfs`)
- begrensde, deterministische quick probe

**Nooit** `stress-ng`, Prime95 of vergelijkbare duurbelasting. Geen
microcode-/BIOS-update.

## 5. GPU-baseline (`gpu_baseline_diagnostics.py`)

Hergebruikt `gpu_detection.build_gpu_report` als enige inventarisbron en
voegt toe:

- render-nodes (`/dev/dri/renderD*`)
- kernel-/firmwarefouten (hang, reset, fence-timeout, Xid)
- optionele read-only probes: `glxinfo` / `eglinfo` / `vulkaninfo`

Ontbrekende driver/firmware → typisch `yellow`/`review_required`. Kritieke
kernel-GPU-fouten → `red`. Geen driver-installatie, geen
modprobe-/cmdline-schrijfacties.

## 6. HDD- / SATA-SSD- / NVMe-baseline

Gemeenschappelijke laag: `storage_baseline_diagnostics.py` (kernel-I/O-fouten,
toolbeschikbaarheid). Apparaatklassen:

| Klasse | Module | Typische bronnen |
|---|---|---|
| HDD | `hdd_baseline_diagnostics.py` | `smartctl`-attributen (o.a. 5/197/198/199/194) |
| SATA-SSD | `sata_ssd_baseline_diagnostics.py` | slijtage/spare/uncorrectable/CRC, TRIM |
| NVMe | `nvme_baseline_diagnostics.py` | `nvme smart-log` / `nvme id-ctrl` |

Alleen **bestaande** SMART-/NVMe-attributen worden gelezen. Een SMART-selftest
(`smartctl -t`, uitgebreide NVMe-selftests) wordt **nooit automatisch** gestart.

## 7. Grenzen van de snelle tests

- 🟢 `green` / `no_immediate_issue_detected` betekent **niet** dat hardware
  foutvrij of langdurig stabiel is.
- Een quick probe dekt slechts een minuscuul geheugen-/CPU-deel.
- Ontbrekende tools leveren `test_unavailable` / `gray`, niet „alles goed”.
- Uitgebreide tests (Memtest86+, SMART-selftest, GPU-render-stress) liggen
  buiten dit snelle pad.

## 8. `HardwareBaselineGate`

Implementatie: `backend/rescue/hardware_baseline_gate.py`.

Velden (additief t.o.v. `core.safety_facade`, **nooit** een bypass):

| Veld | Rol |
|---|---|
| `backup_allowed` | read-only noodbackup blijft in principe mogelijk |
| `restore_allowed` | restore alleen zonder rode data-critical bevindingen en na volledige checks |
| `os_installation_allowed` | OS-installatie analoog aan restore |
| `gui_mode_allowed` | GUI alleen zonder rode GPU-bevinding |

Beide lagen moeten akkoord zijn: baseline-gate **én** `safety_facade`.

## 9. Gevolgen van kritieke bevindingen

| Bevinding | Effect |
|---|---|
| Rood bij geheugen / CPU / storage (geaggregeerd) | blokkeert restore en OS-installatie |
| Rood bij GPU | blokkeert GUI (`gui_mode_allowed=false`), **niet** backup |
| Rode **bron**-schijf | blijft backupbaar (lezen is het doel van noodbackup) |
| Rode **doel**-schijf | nooit schrijfbaar voor backupbestemming, restore of OS-installatie |

Evaluatie per operatie: `evaluate_operation_against_baseline_gate`.

## 10. API-routes (read-only / begrensd)

Module: `backend/api/routes/rescue_hardware_baseline.py`.

| Methode | Pad | Doel |
|---|---|---|
| `GET` | `/api/rescue/hardware/baseline/status` | gate-/runstatus of `{has_run:false}` |
| `POST` | `/api/rescue/hardware/baseline/quick` | snelle baseline starten |
| `POST` | `/api/rescue/hardware/baseline/extended-preview` | dezelfde checks, aanbevelingen benadrukt |
| `GET` | `/api/rescue/hardware/baseline/latest` | laatste volledige run |
| `GET` | `/api/rescue/hardware/baseline/memory` | geheugen-subsystem |
| `GET` | `/api/rescue/hardware/baseline/cpu` | CPU-subsystem |
| `GET` | `/api/rescue/hardware/baseline/gpu` | GPU-subsystem |
| `GET` | `/api/rescue/hardware/baseline/storage` | alle storage-resultaten |
| `GET` | `/api/rescue/hardware/baseline/storage/{device_id}` | één apparaat |

Geen route start installaties, firmware-updates, formatteren of SMART-selftests.

## 11. Uitgebreide tests vereisen operatorbevestiging

`ExtendedTestRecommendation.operator_confirmation_required` is standaard
`true`. `/extended-preview` toont alleen aanbevelingen (`memtest86plus`,
`cpu_stress`, `gpu_render_stress`, `smart_self_test_short`, …) en start geen
langdurige test. Elke uitgebreide test vereist een **expliciete, aparte
operatoractie** buiten deze API.

## 12. Privacy

Baseline-telemetrie volgt `telemetry_redaction_contract.py` /
`hardware_dcc_status.py`: **geen serienummers, geen MAC-adressen, geen
IP-adressen** in telemetry-payloads. Device-ID’s blijven technische
block-devicenamen (bijv. `sda`, `nvme0n1`), geen hardwareseries.
