# ASUS-02 Boot 18:50 UTC — Datenreview

Payload auf Stick: `6635ff89…` (VT-Release-Fix) · Profil **ASUS-02** · Stamp `20260807_185015`

## Operator-Beobachtung (bestätigt durch Daten)

| Beobachtung | Daten |
|---|---|
| Keine GUI | `gui_started=false`, Code `openvt_console_2_not_released` |
| TUI gestartet | `setuphelfer-rescue-tui` auf tty1; Fallback `tui_rerendered_after_gui_failure=true` |
| Meldung GUI fehlgeschlagen | erwartet nach GUI-Fail |
| Konsolenmeldungen stören TUI | Ownership blieb zeitweise `gui_transition`; Kernel/journal auf tty0 |

## Was der letzte Fix schon brachte

- `CHECK_TTY tty1=kept_until_openvt` — kein vorzeitiger VT-Wechsel
- `VT_RELEASE vt=2` lief
- DRM weiter OK (`amdgpudrmfb`, eDP-1 connected)
- 0 failed units

## Warum GUI trotzdem fehlschlug

1. `openvt` VT2: weiter `Konsole 2 konnte nicht freigegeben werden`
2. Journal **18:50:13 `systemd[1]: Reloading`** direkt nach `systemctl mask --runtime getty@tty2` → reißt die GUI-Kette ab
3. Deshalb keine Alternativ-VT-Versuche / kein `OPENVT_FAIL` im Log — Prozess endete abrupt (`KIOSK_PID_EXIT` nach 4s)

## Nächster Workspace-Fix (vorbereitet)

- Kein `systemctl mask` mehr (nur `stop`)
- Default **VT7** + `startx … vt7` vor openvt
- Console quiet + `tui_owned` nach GUI-Fail / beim TUI-Start
