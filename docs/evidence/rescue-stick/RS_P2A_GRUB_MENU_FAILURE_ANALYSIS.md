# RS-P2A GRUB Menu Failure Analysis

**Root Cause:** GRUB gfxmenu lud Hintergrund-JPEG, platzierte echte `menuentry`-Einträge bei `top=52%` über die im Mockup gemalten Pseudo-Buttons. Ergebnis: sichtbares Wallpaper, unsichtbares Menü.

**Zusatz:** `timeout_style` fehlte explizit; Menüband ohne ausreichenden Kontrast.

**Fix:** Menüband nach oben (`top=10%`), `desktop-color`, Titeltext, Scrollbar, `set timeout_style=menu`, `setuphelfer_kiosk=1` im Standard-`menuentry`.
