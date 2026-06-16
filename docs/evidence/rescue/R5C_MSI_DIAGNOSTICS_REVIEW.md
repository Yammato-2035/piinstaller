# R.5C — MSI Diagnostics Review

**Datum:** 2026-06-13

## Datenlage

**Keine** `hardware/msi_diagnostics_latest.{md,json}` auf Stick.

## Erwarteter Inhalt (nach erfolgreichem Boot)

Redacted Auswertung geplant für:

- Hersteller/Modell (z. B. MSI Laptop)
- UEFI/BIOS-Version
- CPU/RAM/GPU
- NVMe/SATA/USB-Topologie (read-only)
- Windows-/Linux-Indizien
- BitLocker-Indizien (ohne Keys)
- WLAN-/Ethernet-Adapter
- interne Datenträger read-only Status

## Aktueller Status

| Feld | Wert |
|------|------|
| MSI-Diagnose ausgeführt | **nein** (nicht nachweisbar) |
| Evidence-Dateien | **fehlen** |
| Ampel | **red** |

## Nächste Aktion

1. MSI vom Stick booten (UEFI-Eintrag SETUPHELFER)
2. Start-Assistant / Evidence-Spool laufen lassen
3. Sauber herunterfahren
4. Stick am Dev-Rechner erneut inventarisieren

## Redaction

Keine Seriennummern, MAC-Adressen oder WLAN-PSKs in committed Evidence.
