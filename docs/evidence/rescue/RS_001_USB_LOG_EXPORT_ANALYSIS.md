# RS-001 USB Log Export Analysis

**Datum:** 2026-06-10  
**Stick:** `/dev/sdb1` (SETUPHELFER)  
**SquashFS:** `0b303d3ab563f4aeaa354813dcbf46e8fb934a3f23d4705251129f80f2ac51dc`  
**Quelle:** Read-only Mount + Operator-Befund

---

## Auf Stick gefundene Dateien (Host-Readback)

| Pfad | Vorhanden |
|------|-----------|
| `setuphelfer/logs/` | **no** |
| `setuphelfer/evidence/boot/` | **no** |
| `setuphelfer/state/` | **no** |
| `setuphelfer/rescue/evidence.json` | **yes** (Writer-Metadaten, alt) |
| `setuphelfer/rescue/version.json` | **yes** |
| `setuphelfer/rescue/boot-branding.txt` | **yes** |
| `boot/grub/grub.cfg` | **yes** (ohne Theme) |
| `boot/grub/themes/setuphelfer/` | **no** |

Kopie: `docs/evidence/runtime-results/rescue/rs001_hardware_retest_latest_from_usb/`

---

## Pflichtfragen

| Frage | Antwort |
|-------|---------|
| `rescue-ui-status.json` auf Stick geschrieben? | **Nein** (Verzeichnis `evidence/boot/` fehlt auf Host-Readback) |
| `display_mode` | Operator: **fallback_tui** (inferiert aus sichtbarem Notmenü) |
| `menu_visible` | **yes** (Fallback-TUI) |
| `browser_candidate` | **keiner** (kein grafischer Browser im SquashFS) |
| `browser_started` | **no** |
| `network_required` | **no** (korrekt offline-first) |
| `telemetry_required` | **no** |
| Warum React nicht sichtbar? | **blocked_missing_browser_or_display_runtime** — `setuphelfer.list.chroot` enthält weder Chromium/Firefox noch Xorg/Wayland/Kiosk |
| Netzwerk-Crash Ursache | **whiptail + set -e/pipefail + fehlende TTY-Umleitung** beim Aufruf aus Fallback-TUI; `grep`/`nmcli`-Pipeline konnte Skript beenden statt ins Menü zurückzukehren |
| Dateien auf Stick geschrieben | Operator meldet Log-Export OK; Host-Readback zeigt nur Writer-Metadaten — Live-Session-Spiegel vermutlich nicht persistiert oder Stick nach Boot nicht erneut gespiegelt |

---

## Operator-Befund (Hardware 1.7.10.1)

```text
UEFI: reached
GRUB: reached (ohne Logo/Theme)
React/Kiosk: no
Fallback TUI: yes
Status action: works
Log export action: works (Operator)
Network action: crashes (Operator)
failed Units im Notmenü: not visible
Live-Medium warning: not visible in screenshots
```

Screenshots: `A2F275B8-…`, `B4095FA5-…`, `448589D2-…`

---

## Fix (Workspace 1.7.10.2, nicht auf Stick)

- Fallback-TUI UX + Status-Kurzfassung
- Netzwerk crash-safe (`set +e`, TTY-Override, `return_to_menu`)
- GRUB-Theme-Staging für FAT32 ESP

**Retest:** Rebuild SquashFS + ggf. GRUB-Theme auf ESP + Verify Hash + Hardware
