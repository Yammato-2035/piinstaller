# Rescue GUI Autostart Contract (RS-P2A)

1. Backend startet im Rescue-Modus (`setuphelfer-rescue-backend-start.sh`).
2. Grafische GUI ist Standard (`setuphelfer-rescue-gui-start.sh` → Kiosk/startx).
3. Text-TUI nur bei Fehler mit klarem `reason`-Code in SETUP_LOGS.
4. Kein Backup-/Restore-Execute durch GUI-Start.
