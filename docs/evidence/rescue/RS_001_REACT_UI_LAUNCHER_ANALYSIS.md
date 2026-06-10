# RS-001 React UI Launcher — Analyse

**Datum:** 2026-06-10  
**HEAD:** `4aed483` → Fix `1.7.10.2`  
**Stick-Version:** `1.7.10.1` (SquashFS `0b303d3…`)

---

## Hardware-Befund (Retest 2026-06-10)

| Beobachtung | Ergebnis |
|-------------|----------|
| UEFI / GRUB / Live | **ja** |
| GRUB Logo/Theme | **nein** |
| React/Kiosk | **nein** |
| Fallback-TUI | **ja** |
| Status-Aktion | **funktioniert** |
| Log-Export | **funktioniert** (Operator) |
| Netzwerk verbinden | **stürzt ab** |
| failed Units im Notmenü | **nicht sichtbar** |

---

## Pflichtentscheidung

```text
React/Kiosk: blocked_missing_browser_or_display_runtime
```

**Begründung:** `setuphelfer.list.chroot` enthält weder `chromium`/`firefox` noch `xorg`/`wayland`/`cage`. HTTP-Server startet; kein grafischer Browser → Launcher fällt korrekt auf Fallback-TUI.

```text
Fallback-TUI: akzeptabler Zwischenmodus für RS-001 (yellow), nicht finales Produktziel
```

Netzwerk-Crash: **Launcher/whiptail/TYY + set -e**, nicht fehlender React-Server.

---

## USB-Log-Analyse (Host-Readback)

| Feld | Wert |
|------|------|
| `rescue-ui-status.json` auf Stick | nicht gefunden |
| `display_mode` (Operator) | `fallback_tui` |
| `browser_candidate` | keiner |
| `browser_started` | no |
| `server_started` | yes (inferiert) |

Details: `RS_001_USB_LOG_EXPORT_ANALYSIS.md`

---

## Fix (1.7.10.2)

| Bereich | Änderung |
|---------|----------|
| Fallback-TUI | Setuphelfer-Notmenü, Status-Kurzfassung, sicheres Netzwerk |
| Netzwerk | crash-safe, `return_to_menu`, non-fatal exit |
| React/Kiosk | **kein apt** — Browser-Package-Plan dokumentieren für späteren SquashFS-Rebuild |
| GRUB | separater Track — `RS_001_GRUB_BRANDING_ANALYSIS.md` |

---

## Browser-Package-Plan (später, nicht dieser Lauf)

Für echtes React/Kiosk im Live-System (separater Build-Prompt):

- `chromium` oder `firefox-esr` + minimaler Display-Stack (z. B. `xorg` + `openbox` oder `cage`)
- Launcher: Kiosk-Start nur nach erfolgreichem Display-Check
- RS-001 green weiterhin: nutzbares Menü (Kiosk **oder** akzeptables Fallback ohne Crash)

---

## Next

Rebuild SquashFS `1.7.10.2` + ESP-Theme-Update + Hardware-Retest.
