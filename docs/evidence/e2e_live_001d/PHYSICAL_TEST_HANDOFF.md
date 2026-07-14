# Physical MSI Test Handoff — SETUPHELFER-E2E-LIVE-001D

## Build

| Feld | Wert |
|------|------|
| Payload-Version | `1.10.0.21` |
| Payload-SHA256 | `55610ae4926a5a9f126a695e77c399125bdeabbcb52bd8e130587ca9db615bd7` |
| Vorherige Version (Stick) | `1.10.0.20` |
| Buildmodus | `payload_repack` |
| USB-Update | `2026-07-14T14:31:52Z` (atomar, erfolgreich) |

## Git

| Feld | Wert |
|------|------|
| Branch | `pi-rs-e2e-live-001d-physical-backup-restore` |
| Feature-HEAD (Build) | `21fa7b5b` + Versions-/Build-Evidence-Commits |
| Stick-Gerät | Intenso Ultra Line `/dev/sda` |

## TUI-Ablauf am MSI

1. Vom Stick booten (Payload `1.10.0.21` prüfen)
2. Stabile TUI abwarten (MSI-Compat, kein GUI-Autostart)
3. Menü: **„E2E Backup-/Restore-Test“**
4. Telemetrie-Consent: **Zustimmen und senden** (für Live-Nachweis)
5. Operator-Gate im Assistenten lesen und bestätigen

## Externes Testmedium

- Dediziertes externes USB-/HDD-Testziel mit ausreichend freiem Speicher (≥ 512 MiB)
- Restore-Ziel: **separates, zunächst leeres** Verzeichnis auf demselben oder einem zweiten externen Medium
- **Nicht** erlaubt: interne NVMe/SATA, SETUPHELFER, SETUP_LOGS, Systempartitionen

## Laufzeit-Konfiguration (nicht im Image)

```text
SETUPHELFER_RS_TELEMETRY_LAB_TOKEN_FILE=<Pfad zur Laufzeit-Token-Datei>
SETUPHELFER_RS_TELEMETRY_ENDPOINT=https://telemetrie.setuphelfer.de/v1/telemetry/ingest
```

Der Lab-Token wird **nicht** im Payload, Build oder dieser Doku gespeichert.

## Telemetrie-Endpunkt

```text
https://telemetrie.setuphelfer.de/v1/telemetry/ingest
```

## Evidence-Pfade (SETUP_LOGS)

```text
setuphelfer/evidence/e2e/<PHYSICAL_E2E_RUN_ID>/
  event-journal.jsonl
  receipts.json
  diagnostics-status.json
  backup-result.json
  verify-result.json
  restore-result.json
  source-summary.json
  restored-summary.json
  manifest-comparison.json
  e2e-result.json
```

Import nach Entwicklungsrechner:

```text
docs/evidence/e2e_live_001d/physical_run/<PHYSICAL_E2E_RUN_ID>/
```

## Abbruchbedingungen

```text
STOP — physical_test_storage_not_confirmed
STOP — unsafe_restore_target
STOP — operator_gate_blocked
STOP — consent_not_granted (nur für Live-Telemetrie-Nachweis)
```

## Status

```text
implemented_pending_physical_msi_test
production_ready=false
```
