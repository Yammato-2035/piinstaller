# Boot4 Test Contract — PI-RS-ASUS-HIGHINFO-PHYSICAL-009

## Carrier gate

**`carrier_1_10_6_1_verified`** · `carrier_version_consistency=passed`

| Field | Value |
|-------|-------|
| Test-ID | `PI-RS-ASUS-HIGHINFO-PHYSICAL-009` |
| Physical Boot | **Boot4** |
| Hardware | ASUS ROG Strix G513QM |
| Payload | `1.10.6.1` |
| Profile | `ASUS-TUI-BASELINE-HIGHINFO` (GRUB default) |
| NVME_WRITE_ALLOWED | **false** |

## Operatorablauf

1. Stick am ASUS im UEFI booten (Default belassen).
2. TUI vollständig starten lassen.
3. Netzwerk verbinden (WLAN oder LAN).
4. Mindestens 2–3 Minuten im laufenden System bleiben.
5. **Kein** Installer, **keine** NVMe-Änderung.
6. Kontrolliert herunterfahren.
7. Stick zurück / SETUP_LOGS Evidence liefern.

## Automatisch zu erwarten (nach 1.10.6.1)

- `boot/highinfo/xorg_probe_evidence.json` (auch bei Fail/Skip)
- startx forensic unter SETUP_LOGS wenn Probe lief
- Telemetrie-Versuch + ACK/`correlation_id` soweit Netz erreichbar
- Hardware/SMART/NVMe read-only
- Install-readiness Inputs (ohne Write)

## Verboten

Installer · mkfs · parted · NVMe write · EFI write · Windows · BitLocker · BIOS
