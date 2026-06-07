# RESCUE Network Onboarding, Telemetry Push & Controlled Task Pull

**Datum:** 2026-06-07  
**Version:** `1.7.5.0` (Minor-Funktionserweiterung: Network-Onboarding + Telemetry-Push + Task-Pull)  
**Vorher:** `1.7.4.6`

## Ergebnis

| Komponente | Status |
|------------|--------|
| MSI-Befund ingestiert | ja — `RESCUE_MSI_NETWORK_ONBOARDING_FAILURE_TRIAGE.md` |
| Paketliste erweitert (rfkill, iw, pciutils, …) | ja |
| `setuphelfer-rescue-network-onboarding` | ja |
| `setuphelfer-rescue-media-check` | ja |
| `setuphelfer-rescue-telemetry-push` | ja |
| `setuphelfer-rescue-task-pull` | ja |
| systemd-Units + Boot-Menü-Hook | ja |
| Backend Task-Pull API | ja |
| Boot-Network-Telemetrie-Ingest-Schema | ja |
| LAN-Proxy Task-Pfade (optional abschaltbar) | ja |
| DCC Gate/Kachel | ja |
| ISO-Rebuild / USB-dd | **nein** (Operator-Handoff) |
| MSI-Retest | **nein** (kein Fake-Green) |
| Windows-Inspect | **blockiert** |

## Gate (ehrlich)

```text
target_laptop_booted_from_stick: true (Operator-Befund ingestiert, neues ISO noch nicht deployed)
target_live_media_runtime_stable: false (bis Rebuild+MSI-Validierung)
target_network_onboarding_available: true (Code im Workspace)
target_network_link_established: false (WLAN-Onboarding fehlte auf altem Stick)
target_telemetry_health_reached: false
target_telemetry_ingest_ack: false
controlled_task_pull_available: true (Backend)
windows_inspect_executable: false
```

## Operator ISO-Rebuild-Handoff

```bash
cd /home/volker/piinstaller
sudo bash scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean
./scripts/rescue-live/prepare-controlled-live-build-tree.sh
./scripts/rescue-live/validate-controlled-live-build-tree.sh build/rescue/live-build/setuphelfer-rescue-live
export RESCUE_MSI_FIRMWARE_REBUILD_FREIGEGEBEN=1
sudo ./scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build
```

Danach: UEFI-Validator, SquashFS-Check, Script-Präsenz, separater USB-Rewrite-Prompt.

## MSI Live-Befehle (nach Rebuild)

```bash
sudo setuphelfer-rescue-network-onboarding
sudo setuphelfer-rescue-media-check
sudo setuphelfer-rescue-telemetry-push
sudo setuphelfer-rescue-task-pull
```

Telemetrie-URL: `http://192.168.178.140:8001/api/rescue/telemetry/health`

## Nächster Prompt

`RESCUE_ISO_NETWORK_ONBOARDING_REBUILD_AND_USB_REWRITE_OPERATOR_RUN`
