# RS-P2C GRUB Failsafe Menu Fix

## Änderungen

- `generate_grub_cfg_failsafe_plain_lines()` — kein `set theme=`, kein gfxmenu/jpeg.
- `menu_color_normal=white/black`, `menu_color_highlight=black/white`.
- `set timeout=15`, `set timeout_style=menu`, `set default=0`.
- 7 `menuentry` (5 Live + Neustart + Ausschalten).

## Einträge

1. **Sicherer Textmodus** — `setuphelfer_mode=text setuphelfer_kiosk=0 setuphelfer_safe_ui=1` (Default)
2. **Grafische Oberfläche** — `setuphelfer_mode=gui setuphelfer_kiosk=1 setuphelfer_gui_watchdog=1`
3. **Diagnose sammeln** — `setuphelfer_mode=diagnostics setuphelfer_collect_diagnostics=1`
4. **Hardware/WLAN** — `setuphelfer_mode=hardware setuphelfer_wifi_diag=1`
5. **MSI/NVIDIA Text-Kompat** — `nomodeset nouveau.modeset=0`
6. Neustart / Ausschalten

## Statische Checks (Workspace)

| Check | Ergebnis |
|-------|----------|
| menuentry ≥ 6 | 7 |
| setuphelfer_mode=text Default | ja (Eintrag 0) |
| setuphelfer_kiosk=0 Default | ja |
| setuphelfer_kiosk=1 nur GUI | ja |
| timeout_style=menu | ja |
| kein Theme/Wallpaper-Menü | ja |
| keine 52%-Button-Koordinaten | ja |
