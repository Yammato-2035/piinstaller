# FAQ – Rescue GUI / VT / Fortschritt (de-DE)

1. **Warum startet die grafische Oberfläche nicht?** Oft erkennt der Watchdog die Kiosk-URL nicht oder der GUI-VT ist nicht aktiv — siehe Root-Cause VT-PROGRESS-002.
2. **Was bedeutet openvt_console_2_not_released?** Historischer/fehlerhafter Code; Kiosk nutzt typischerweise VT7. Prüfen Sie aktuelle `gui-start.log`.
3. **Was ist ein virtuelles Terminal?** Eine Linux-Textkonsole (tty1…); GUI läuft auf einem reservierten VT.
4. **Läuft BVR bei GUI-Fallback weiter?** Ja — Watchdog fällt auf TUI zurück, BVR-Kern bleibt aktiv.
5. **Warum springt die Fortschrittsanzeige?** Widersprüchliche Quellen; kanonisch ist `canonical-bvr-progress.json`.
6. **Warum SABRENT obwohl fertig?** Veraltetes `auto-e2e-state`; Driftcode `rescue.bvr.progress_source_drift`.
7. **Welche Fortschrittsquelle ist verbindlich?** `canonical-bvr-progress.json`.
8. **Veraltete Statusdatei?** Letzter gültiger Snapshot bleibt; Warnung wird gesetzt.
9. **Warum ist DCC im Release eingeschränkt?** Developer-Capability schützt Dev-APIs; Release nutzt `/api/status/rescue-bvr`.
10. **Welche Rescue-Infos sind im Release sichtbar?** Redigierter read-only Status ohne Secrets/Pfade.
11. **Was bedeutet msi_compat_nomodeset?** MSI-Kompatibilitätsprofil; unter `mode=gui` bleibt GUI-Versuch erlaubt.
12. **Wann ist der MSI-Test vollständig bestanden?** HTTP+X11+Chromium sichtbar, Fortschritt synchron, BVR grün, VT freigegeben, Auto-Shutdown.
13. **Wat was het resultaat van retest 1.10.1.2 (002R)?** BVR op MSI GE63 geslaagd (`…-05b6f187`); HTTP ready en VT7 voorbereid; operator zag **geen** GUI → status `passed_with_gui_fallback`, niet `passed`.
