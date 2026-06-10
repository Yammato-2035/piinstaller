# RS-001 React Rescue Hardware Retest — Ergebnis

**Datum:** 2026-06-10  
**Commit (Stick-Payload):** `bc75f89`  
**Fix (Workspace):** `1.7.10.2`  
**Version auf Stick:** `1.7.10.1` (SquashFS)  
**RS-001 Status:** **yellow**  
**Lauf-Status:** **Hardware-Retest durchgeführt — Fallback-TUI OK, React/GRUB-Branding/Netzwerk-Crash offen**

---

## Hardware-Befund (Operator, Payload `0b303d3…`)

| Feld | Wert |
|------|------|
| UEFI | **reached** |
| GRUB | **reached** |
| GRUB logo/theme visible | **no** |
| React/Kiosk UI visible | **no** |
| Fallback TUI visible | **yes** |
| Fallback TUI status action | **works** |
| Fallback TUI log export action | **works** |
| Fallback TUI network action | **crashes** |
| Old whiptail blocker | **no** |
| Live-Medium warning | **not visible** in screenshots |
| network/telemetry/wait-online failed in beginner flow | **not visible** in screenshots |
| Screenshots | `A2F275B8-…`, `B4095FA5-…`, `448589D2-…` |

---

## Klassifikation

```text
RS-001: yellow
Reason: fallback menu reached and partial functions work; GRUB branding missing; React/Kiosk unavailable; network menu crashes
```

**Nicht grün** — kein React/Kiosk; Netzwerk-Aktion instabil; GRUB ohne Branding.

---

## Workspace-Fix (1.7.10.2)

| Bereich | Fix |
|---------|-----|
| GRUB Branding | Theme-Staging auf FAT32 ESP + gfx-Module + `set theme=` |
| Fallback TUI | Setuphelfer-Notmenü, Status-Kurzfassung, Details optional |
| Netzwerk | crash-safe: `set +e`, TTY-Override, `return_to_menu`, non-fatal exit |
| React/Kiosk | dokumentiert: Browser/Display fehlt im SquashFS — kein apt in diesem Lauf |

---

## Next

1. Rebuild/update SquashFS mit `1.7.10.2`
2. GRUB-Theme + ggf. `grub.cfg` auf FAT32 ESP aktualisieren (separater Payload-Lauf)
3. Verify Hash Gate
4. Hardware-Retest: GRUB-Branding + Fallback ohne Netzwerk-Crash; React optional erst nach Browser-Package-Plan
