# RS-P2A WiFi Fix Result

- `setuphelfer_rescue_wifi_ensure_managed()` erweitert: rfkill, modprobe iwlwifi, `ip link up`, unavailable→managed, NM-Restart bei WIFI-HW-missing+iw-Interface
- `setuphelfer_rescue_wifi_prepare_radio()` vor Scan in network-onboarding
- HDD-Backup bleibt unblocked (`blocks_local_hdd_backup=false`)
- **runtime_validated:** yellow — MSI-Retest RS-P2B
