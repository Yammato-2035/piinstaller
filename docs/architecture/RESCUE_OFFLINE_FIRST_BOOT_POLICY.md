# Rescue Offline-First Boot Policy

**Version:** 1.7.10.0

## Pflichtregeln

1. Rescue-Stick muss **ohne Netzwerk** bis zum lokalen Hauptmenü booten.
2. Netzwerk darf **nie** Boot-Voraussetzung sein.
3. WLAN-Suche erfolgt **nur nach Nutzerwahl**.
4. Telemetrie ist standardmäßig **deaktiviert**.
5. Telemetrie erfordert **Opt-in** oder Debug-Modus.
6. Fehlendes Netzwerk = `review_required`, nicht `failed`.
7. Fehlende Telemetrie = `skipped`, nicht `failed`.
8. Live-Medium-Stabilität bewertet nur Medium, Squashfs, Evidence, Hash, Pflichtdateien.
9. Optional-Service-Failures dürfen **keine** Live-Medium-Warnung auslösen.
10. Erster Nutzerscreen = ruhiges Setuphelfer-Hauptmenü (React), nicht whiptail-Wizard.

## UX-Blocker (IST)

Alter `setuphelfer-rescue-start-assistant` erzwingt whiptail-Schritte für Medium/Netzwerk/Telemetrie vor Nutzwert.

## Ziel

React Rescue Shell ersetzt primären Bootflow; Textmodus nur Fallback.
