# Windows 11 — Rescue-Stick Boot + Read-only Inspect

**BLOCKIERT (2026-06-05):** `RESCUE_USB_UEFI_BOOT_FAILURE_MSI_WINDOWS11` — aktuelle ISO ist nur BIOS/ISOLINUX-hybrid; MSI W11 UEFI-Boot fehlgeschlagen. Windows-Inspect erst nach `RESCUE_ISO_UEFI_X64_REBUILD_OPERATOR_RUN` + Validator grün + bestätigtem UEFI-Boot.

**Voraussetzung:** UEFI-x64-fähige Setuphelfer-ISO (`validate-rescue-iso-uefi-boot.sh` Exit 0), dann USB-Stick geschrieben (Operator-Handoff)
**Zielgerät:** Windows-11-Pro-Laptop (2×2 TB NVMe, AMD, NVIDIA) — **nicht** der Developer-Laptop als Ersatz

## 1. Vorbereitung

- [ ] ISO auf USB geschrieben (`RESCUE_USB_WRITE_OPERATOR_HANDOFF_FOR_WINDOWS_INSPECT.md`)
- [ ] Windows-Laptop herunterfahren
- [ ] Rescue-USB einstecken
- [ ] Netzwerk für Telemetrie später prüfen

## 2. Boot

1. UEFI-Bootmenü öffnen (Hersteller-Taste, z. B. F12/F2/Esc)
2. **USB / UEFI: Setuphelfer** wählen
3. **Keine** Windows-Reparatur, **kein** Installationsassistent auf Platte

## 3. Nach dem Boot (Rescue-Linux)

- Kein Partitionieren, kein NTFS-Write, kein BitLocker-Unlock
- Netzwerk prüfen (Telemetrie-ACK später Pflicht)

## 4. Read-only Inspect

```bash
cd /path/to/setuphelfer-on-stick-or-mount
bash scripts/windows-rescue/plan-windows-readonly-inspect.sh \
  docs/evidence/windows-rescue/operator_windows_readonly_plan_latest.json
bash scripts/windows-rescue/ingest-operator-hardware-run.sh
```

## 5. BitLocker zuerst

- Status **unknown** → kein Dateizugriff
- Erst bei `not_detected` / sicher read-only zugänglich: Registry/Explorer-Hinweise

## 6. Telemetrie

- Report senden, **ACK + Hash-Match** dokumentieren
- Ohne ACK: **gelb**, kein Grün

## 7. Evidence ins Workspace (Developer-Maschine)

JSON-Dateien kopieren — **keine** Secrets, **keine** Dateiinhalte:

- `operator_windows_readonly_plan_latest.json`
- `windows_inspect_report_latest.json`
- `windows_rescue_telemetry_envelope_latest.json`
- optional `operator_telemetry_ack_latest.json`

## Verboten

Reparatur, Cloud-Backup mit Credentials, Repartition, Dualboot-Install, Bootloader-Schreiben

## Upstream-Blocker (solange offen)

| ID | Bedeutung |
|----|-----------|
| `RESCUE_STICK_NOT_WRITTEN` | Kein USB |
| `RESCUE_USB_BOOT_NOT_VALIDATED_ON_TARGET` | W11 nicht vom Stick gebootet |
