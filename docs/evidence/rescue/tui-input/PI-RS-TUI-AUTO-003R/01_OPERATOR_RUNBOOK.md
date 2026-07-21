# Operator-Runbook – PI-RS-TUI-AUTO-003R

## Vorbereitung
- MSI GE63 Raider RGB 8RF
- Stick Payload **1.10.0.60** (Intenso Ultra Line)
- Optional: kabelgebundene USB-Tastatur (erst auf Aufforderung anschließen)
- Optional: Smartphone für Fotos
- Keine weiteren USB-Datenträger

## 1. Boot
1. Stick in MSI stecken, vom Stick booten.
2. GRUB-Timeout **nicht** ablaufen lassen.
3. **Nur** diesen Eintrag wählen:

```text
Setuphelfer – TUI-Eingabediagnose (read-only)
```

Nicht: Default Lab-Auto GUI, normaler GUI-, normaler Textmodus.

### Pflichtnotiz GRUB
```text
GRUB sichtbar:
Interne Pfeiltasten funktionieren:
Enter funktioniert:
Diagnoseeintrag vorhanden: ja
Diagnoseeintrag ausgewählt: ja
```

## 2. tty2 Diagnose
Erwartung:
- tty1: normale Setuphelfer-TUI (whiptail)
- tty2: Diagnoseassistent

Max. 90 s warten. Wenn Oberfläche fehlt: einmal `Ctrl+Alt+F2`.

```text
Diagnoseprozess aktiv:
Diagnoseoberfläche sichtbar:
Diagnoseoberfläche lesbar:
Tastatur auf tty2 reagiert:
```

## 3. Persistenzstatus notieren
```text
Runtime-Pfad: /run/setuphelfer/tui-input-diagnostics/<RUN_ID>/
SETUP_LOGS: gefunden | wartet | …
Persistente Speicherung: …
Herunterfahren: gesperrt | freigegeben
RUN_ID=<...>
```

## 4. Interne Tastatur tty2
Auf Aufforderung je einmal: ↑ ↓ ← → Tab Esc Enter A Caps/Num Lock.

## 5. tty1 Menütest
Nur wenn Assistent `write_actions_blocked=true` zeigt.
Dann mit ~2 s Abstand: ↓ ↑ Tab Esc Enter.
Beobachten: Markierung/Flackern/Redraw/Enter/Esc.
Rückkehr tty2 (oder einmal Ctrl+Alt+F2).

## 6. Operatorfragen (J/N/U)
Wie vom Assistenten angezeigt beantworten.

## 7. Externe Tastatur
Nur auf Aufforderung. Sonst: `external_keyboard_test=skipped_not_available`.

## 8. Finalizer / Shutdown
**Nicht** herunterfahren, bis angezeigt:

```text
Evidence dauerhaft gespeichert: …/tui-input-diagnostics/<RUN_ID>/
Manifest: gültig
SHA256: gültig
Herunterfahren: freigegeben
```

Dann sicheren Shutdown des Assistenten nutzen.
**Hinweis:** Menüpunkt „Ausschalten“ in der normalen TUI ist im Diagnosemodus **gesperrt** (absichtlich). Shutdown über den Diagnoseassistenten nach Persistenz, oder Host-Power nach Freigabe.

## 9. Rückkehr
Nach Ausschalten Stick entnehmen und am Dev-PC melden:

```text
STICK ZURÜCK – IMPORT STARTEN
RUN-ID: <RUN_ID>
```

## Wichtig aus vorherigem Versuch
- „Alle Tasten gehen“ = Fortschritt; trotzdem **Diagnose-Eintrag** und **tty2-Assistent** vollständig durchlaufen.
- „Ausschalten geht nicht“ im TUI-Menü bei Diagnose = erwartet; erst nach `shutdown_allowed=true` über Assistenten.
- Ohne Persistenzfreigabe **nicht** hart ausschalten, sonst geht `/run`-Evidence verloren.
