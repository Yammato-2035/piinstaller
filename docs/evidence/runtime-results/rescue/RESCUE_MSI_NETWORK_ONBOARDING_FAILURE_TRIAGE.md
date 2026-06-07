# RESCUE MSI Network Onboarding Failure Triage

**Datum:** 2026-06-07  
**Prompt:** `RESCUE_NETWORK_ONBOARDING_TELEMETRY_PUSH_AND_CONTROLLED_TASK_PULL`  
**ISO SHA256:** `9ef1b330c6ec774dfa1966c2f87c3c3ef31b3adf421f64fa2375c90408f21f3a`  
**USB:** `/dev/sdb` Ultra Line, Serial `24111412110212`

## Operator-Befund (MSI)

| Beobachtung | Status |
|-------------|--------|
| UEFI-Boot vom Rescue-Stick | **ja** (grundsätzlich) |
| Live-System startet | **ja** |
| NetworkManager.service aktiv | **ja** |
| Automatische WLAN-Suche nach Neustart | **nein** |
| SSID-Auswahl / Passwortabfrage | **nein** |
| Frühere WLAN-Verbindung (historisch) | **ja** — IP `192.168.178.96`, Route vorhanden |

## Kernel-/Firmware-Meldungen (MSI)

```text
PCIe Bus Error: severity=Corrected
pcieport ... Corrected error message received from 0000:05:00.0
ACPI Error: No handler for Region [VRTC]
ACPI Error: Region SystemCMOS (ID=5) has no handler
ACPI Error: Aborting method \_SB.PCI0.LPCB.EC._Q9A due to previous error
```

## Bewertung

| Klassifikation | Einordnung |
|----------------|------------|
| Primärproblem | **Fehlendes robustes Netzwerk-Onboarding** nach Boot/Neustart |
| PCIe Corrected | Hardware-Warning — erfassen, nicht als alleinige Root Cause |
| ACPI VRTC/SystemCMOS | Firmware/ACPI-Warning — erfassen, nicht verstecken |
| Windows-Inspect | **blockiert** bis Live-Medium + Netzwerk + Telemetrie validiert |

## Neue Blocker-IDs

- `RESCUE_NETWORK_ONBOARDING_REQUIRED`
- `RESCUE_WIFI_SCAN_NOT_TRIGGERED`
- `RESCUE_WIFI_PASSWORD_PROMPT_MISSING`
- `RESCUE_TELEMETRY_PUSH_NOT_AUTOMATED`
- `RESCUE_CONTROLLED_TASK_PULL_NOT_AVAILABLE`

## Maßnahme (Workspace)

Implementierung von `setuphelfer-rescue-network-onboarding`, Telemetrie-Push, Controlled Task Pull, erweiterte Paketliste und Gate-Felder — siehe `RESCUE_NETWORK_ONBOARDING_TELEMETRY_PUSH_TASK_PULL_RESULT.md`.

ISO-Rebuild und USB-Rewrite: **separater Operator-Prompt** (kein dd in diesem Lauf).
