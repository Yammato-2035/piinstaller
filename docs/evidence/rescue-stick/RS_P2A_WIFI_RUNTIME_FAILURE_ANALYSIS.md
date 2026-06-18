# RS-P2A WiFi Runtime Failure Analysis

| Prüffeld | Befund |
|----------|--------|
| Fix-Funktion im Payload | ja (vor Fix nur unmanaged; unavailable fehlte) |
| Fix vor Scan aufgerufen | teilweise |
| NetworkManager aktiv | ja |
| wlo1 vorhanden | ja (iw) |
| wlo1 unmanaged | nein — unavailable |
| NM WIFI-HW missing | ja trotz iwlwifi-Interface |
| rfkill blockiert | nein |

**Root Cause:** `setuphelfer_rescue_wifi_ensure_managed()` behandelte nur `unmanaged`, nicht `unavailable`/down. Treiber/Firmware nicht vor Scan hochgefahren; NM-Restart fehlte bei WIFI-HW-missing-Fehlindikation.
