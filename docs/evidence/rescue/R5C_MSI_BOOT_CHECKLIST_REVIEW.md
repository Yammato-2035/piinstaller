# R.5C — MSI Boot Operator Checklist (Review)

**Datum:** 2026-06-13  
**Referenz:** `R5B_MSI_BOOT_OPERATOR_CHECKLIST.md`

## Durchführungsstatus

| Schritt | Operator-Ist | Nachweis auf Stick |
|---------|--------------|-------------------|
| MSI ausgeschaltet | *ausstehend* | — |
| Stick eingesteckt | ja (Dev-Rechner) | Layout OK |
| Bootmenü UEFI | *ausstehend* | — |
| GRUB grafisch | *ausstehend* | static: Theme in grub.cfg |
| Setuphelfer-Logo | *ausstehend* | Theme-PNG auf Stick |
| Linux startet | *ausstehend* | — |
| TUI | *ausstehend* | — |
| Browser/Kiosk | *ausstehend* | — |
| React UI | *ausstehend* | — |
| `/setuphelfer-evidence/` | **nein** | **fehlt** |
| WLAN-Menü | *ausstehend* | — |
| Keine destructive Aktion | *Operator-Pflicht* | — |

## GRUB (statisch auf Stick)

- `set theme=` in `boot/grub/grub.cfg`: **ja** (Verbesserung ggü. ISO-Post-Build yellow)
- Menuentries: Standard, Netzwerk, MSI/NVIDIA-Kompat

## Sicherheit

Kein Schreibzugriff auf interne MSI-Datenträger in diesem Review-Lauf.

## Nächster Operator-Schritt

MSI-Boot manuell durchführen, Beobachtungen in dieser Checklist ergänzen, Stick zurück an Dev-Rechner → R.5C erneut Phase 2–8.
