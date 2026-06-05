# Windows 11 — Rescue-Stick Boot + Read-only Inspect

**Status:** `blocked_until_usb_boot`  
**UEFI-ISO:** Validator Exit **0** (SHA256 `09b9482a…`) — UEFI-Blocker behoben  
**Nächster Engpass:** USB-Write + MSI-Laptop-Boot

## Voraussetzungen (Checkliste)

- [x] UEFI-x64-ISO gepatcht und validiert (`validate-rescue-iso-uefi-boot.sh` Exit 0)
- [ ] USB-Stick geschrieben (`RESCUE_USB_WRITE_OPERATOR_HANDOFF_FOR_WINDOWS_INSPECT.md`)
- [ ] MSI/Windows-11-Laptop vom Stick gebootet
- [ ] Telemetrie-ACK nach Inspect

## 1. USB vorbereiten (Operator, Developer-Maschine)

Siehe: `docs/evidence/runtime-results/rescue/RESCUE_USB_WRITE_OPERATOR_HANDOFF_FOR_WINDOWS_INSPECT.md`

**Nicht** `sda` (Backup), **nicht** NVMe.

## 2. Boot am MSI/Windows-11-Laptop

1. Stick einstecken, Laptop herunterfahren/neu starten
2. UEFI-Bootmenü (Hersteller-Taste)
3. **Secure Boot** für diesen Test **aus**
4. **USB / UEFI: Setuphelfer** wählen — keine Windows-Reparatur auf Platte

### Boot-Ergebnis dokumentieren

| Frage | ja/nein |
|-------|---------|
| GRUB/Bootmenü sichtbar? | |
| Linux startet? | |
| Login möglich? | |
| Netzwerk vorhanden? | |
| Telemetrieserver erreichbar? | |

Bei erneutem UEFI-Fehler: **nicht** Windows-Inspect — Triage `RESCUE_USB_UEFI_BOOT_FAILURE_MSI_WINDOWS11`.

## 3. Read-only Inspect (erst nach erfolgreichem Boot)

- BitLocker-Status zuerst — **unknown** → kein Dateizugriff
- Kein NTFS-Schreiben, kein Partitionieren, kein BitLocker-Unlock
- Nur read-only Plan:

```bash
bash scripts/windows-rescue/plan-windows-readonly-inspect.sh \
  docs/evidence/windows-rescue/operator_windows_readonly_plan_latest.json
bash scripts/windows-rescue/ingest-operator-hardware-run.sh
```

## 4. Telemetrie

- Envelope senden (`/api/rescue/telemetry/v1/ingest`)
- **ACK + Hash-Match** dokumentieren
- Ohne ACK: Status **gelb**, kein Fake-Green
- Telemetrie unabhängig vom DCC-Gate (`RESCUE_TELEMETRY_INGEST_ENABLED=1`)

## 5. Evidence (Developer-Maschine)

JSON ins Workspace kopieren — **keine** Secrets, **keine** Dateiinhalte:

- `operator_windows_readonly_plan_latest.json`
- `windows_inspect_report_latest.json`
- `windows_rescue_telemetry_envelope_latest.json`

## Verboten

Reparatur, Repartition, Dualboot-Install, Bootloader-Schreiben auf Windows-Platten

## Upstream-Blocker (aktuell)

| ID | Status |
|----|--------|
| `RESCUE_ISO_UEFI_X64_NOT_READY` | **behoben** |
| `RESCUE_STICK_NOT_WRITTEN` | offen |
| `RESCUE_USB_BOOT_NOT_VALIDATED_ON_TARGET` | offen |

**Next Prompt:** `RESCUE_USB_WRITE_OPERATOR_FOR_WINDOWS_INSPECT` → danach `WINDOWS11_RESCUE_OPERATOR_HARDWARE_READONLY_RUN`
