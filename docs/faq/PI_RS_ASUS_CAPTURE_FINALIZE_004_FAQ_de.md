# FAQ PI-RS-ASUS-CAPTURE-FINALIZE-004 (DE)

1. **Warum startet bei der ASUS-Hardwarediagnose keine GUI?** Profil `hardware_discovery` erzwingt Textmodus (`setuphelfer_mode=text`, `skip_gui`). GUI-Status: `not_applicable_for_text_hardware_discovery` — kein Fehler.
2. **Warum ist `nomodeset` aktiv?** Ohne `nomodeset` erzeugte amdgpu auf G513QM ein Dummy-Device und das Panel blieb schwarz. Bleibt für dieses Profil aktiv.
3. **Was bedeutet ein terminaler Diagnosezustand?** `status` ist genau einer von `complete|partial|failed|cancelled` mit `terminal=true`. `running` darf nach Abschluss nicht stehen bleiben.
4. **Wann darf der Stick entfernt werden?** Erst nach sichtbarer Abschlussmeldung und Completion-/Partial-Marker (nach Herunterfahren).
5. **Was passiert, wenn keine Panther-Logs gefunden werden?** Status `windows_setup_logs=not_found` (nicht `failed`) → typisch Retest mit Log-Sammlung.
6. **Warum bleiben vollständige Seriennummern nur auf dem Stick?** Rohwerte nur in `protected_raw` lokal; Git/DCC/Doku nur Hashes/Masken.
7. **Warum reicht das Löschen einer Datei im letzten Commit nicht aus?** Ältere erreichbare Commits behalten Blobs — Historie muss bereinigt oder neu aufgebaut werden.
8. **Was bedeutet `diagnosis_incomplete`?** Capture nicht terminal oder Pflichtbereiche fehlen (z. B. SMART/Finalizer).
