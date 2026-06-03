# Rescue Live Setup Menu Stub Result

**Datum:** 2026-06-03  
**HEAD:** `2ca3a70`

## Komponente

`frontend/src/components/rescue/RescueLiveSetupMenu.tsx`

## Bereiche (Stub/Vorschau)

1. **Sicherheit** — Firewall checked+locked+required; Schreib/Restore/Backup disabled; E2EE required  
2. **Development Server** — Discovery, Pairing, Heartbeat, Report (Stub-Text)  
3. **Hardware** — CPU/RAM/Firmware/Secure Boot/Netz (Stub)  
4. **Festplatten** — Datenträger, Kandidaten, SMART (Stub)  
5. **Bootoptionen** — EFI/OS/Bootloader; Reparatur nur Vorschau  
6. **Diagnose** — lokaler/verschlüsselter Report; USB-Export disabled  
7. **Sprache/Tastatur** — de/en, Layout, Fallback-Textmodus  

## Regeln eingehalten

- Keine Schreib-Buttons aktiv  
- Firewall nicht abwählbar  
- Hinweis: „Vorschau / Sicherheitsmenü – keine Reparatur ohne spätere Freigabe.“  
- i18n via react-i18next + de/en Fallback-Texte  

## Status

**yes** — Stub vorhanden, keine Live-Ausführung auf Rescue-ISO.
