# FAQ PI-RS-ASUS-WIN11-RETEST-005 (NL)

1. **Ist BIOS 331 die Ursache?** Noch nicht belegt — Stage A muss Logs liefern.
2. **Warum zuerst BIOS 331?** Ausgangsbedingung der früheren Abbrüche erhalten.
3. **Warum nicht sofort 335?** Sonst ist Kausalität nicht isolierbar.
4. **Welche Logs?** Panther, Rollback, SetupDiag, DISM/CBS, setupapi, BCD/Disk.
5. **Was ist SetupDiag?** Microsoft-Auswertung von Setup-Abbrüchen.
6. **Warum zweite NVMe isolieren?** Verhindert falsches EFI-/Partitionierungsziel.
7. **Warum nicht beide NVMe?** Windows Setup darf Linux-Platte nicht anfassen.
8. **Wann BIOS-Zusammenhang wahrscheinlich?** 331 fail + 335 pass bei gleichen Konstanten.
9. **Warum beweist Erfolg nach Update nicht alleinige Ursache?** Andere Variablen möglich; nie sole_cause.
10. **Wann Linux?** Erst nach `windows_postcheck_passed` → `ready_for_planning`.
