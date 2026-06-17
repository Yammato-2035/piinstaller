# RS-F2B.1 WLAN Failure Analysis

| Prüffeld | Befund |
|----------|--------|
| WLAN-Hardware erkannt | **ja** (Intel AC 9560, iwlwifi geladen) |
| Kernel-Modul geladen | **ja** (iwlwifi, iwlmvm, mac80211) |
| Firmware fehlt | **nein** (`9000-pu-b0-jf-b0-46.ucode` geladen) |
| rfkill blockiert | **nein** |
| NetworkManager aktiv | **ja** |
| wpa_supplicant vorhanden | unbekannt (nmcli vorhanden im Live-System) |
| nmcli scan lief | **nein** (wlo1 unmanaged, operstate DOWN) |
| WLAN-Interface vorhanden | **ja** (`wlo1`) |
| Treiber-/Firmware-Hinweis | NM meldet `WIFI-HW missing` trotz geladenem iwlwifi; Interface **unmanaged** |
| UI-Fehler sichtbar | **teilweise** (WIFI_CONNECT_FAILED, kein klarer unmanaged-Hinweis) |
| Fallback angeboten | **ja** (offline fortfahren im Netzwerk-Menü) |

## Ergebnislogik

- `wlan_required_for_local_hdd_backup=false`
- `wlan_required_for_cloud_backup=true`
- MSI: `selected_target=external_hdd` + wifi_missing → **warning, not blocker**

## Fix RS-F2B.1

1. `setuphelfer_rescue_wifi_ensure_managed()` — setzt unmanaged WiFi-Geräte auf managed
2. `rescue_wifi_diagnostics.py` — klassifiziert Status für Plan/API
3. `rescue_backup_plan_contract.py` — `wifi_missing_but_not_required` bei external_hdd

## Root Cause (klassifiziert)

**NM unmanaged + WIFI-HW missing (NM-Quirk)** — nicht fehlende Hardware/Firmware.
