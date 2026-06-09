# Rescue Boot Menu UX MVP

**Branding:** Setuphelfer weiß-grün · Companion sichtbar · keine Dashboard-Kacheln

## Hauptmenü

```text
Setuphelfer Rettungsstick

Was möchtest du tun?

> Empfohlen: System sicher prüfen
  Daten retten / Backup finden
  Netzwerk verbinden
  Logs & Diagnose exportieren
  Media-Check / Start in RAM
  Erweiterte Optionen
  Neustart / Ausschalten
```

## Regeln

- Kurze Texte, große Auswahlflächen
- Tastaturbedienung (Enter/Fokus)
- DE/EN umschaltbar
- Keine rohen systemd-Failed-Units im Anfängerbildschirm
- Experteninfos nur unter „Erweiterte Optionen“
- Keine Reparatur/Restore/Installation ohne explizite Bestätigung (MVP: nicht freigegeben)

## Referenz-Assets

- `scripts/rescue-live/image/branding/bootmenu-de.png`
- `scripts/rescue-live/image/branding/bootmenu-en.png`
- `setuphelfer/assets/branding/logo/logo-mascot.png`
