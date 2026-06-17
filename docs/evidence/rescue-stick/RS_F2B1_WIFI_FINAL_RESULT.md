# RS-F2B.1 WLAN Final

- **Ampel:** yellow (Fix im Payload, MSI-Retest offen)
- **Ursache:** wlo1 unmanaged, NM `WIFI-HW missing` trotz iwlwifi
- **Fix:** `nmcli device set … managed yes` vor Scan
- **HDD-Backup:** nicht blockiert
