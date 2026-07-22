# FAQ PI-RS-ASUS-CAPTURE-FINALIZE-004 (NL)

1. **Waarom geen GUI?** Tekstprofiel (`setuphelfer_mode=text`, `skip_gui`). GUI-status: `not_applicable_for_text_hardware_discovery`.
2. **Waarom `nomodeset`?** Zonder dat maakte amdgpu een dummy-device; panel bleef zwart op G513QM.
3. **Terminale status?** Exact één van `complete|partial|failed|cancelled` met `terminal=true`.
4. **Stick verwijderen?** Pas na afrondingsmelding en Completion-/Partial-marker.
5. **Geen Panther-logs?** `windows_setup_logs=not_found` (niet `failed`).
6. **Volledige serienummers?** Alleen lokaal op de stick in `protected_raw`.
7. **Verwijderen in tip-commit?** Onvoldoende als oudere commits bereikbaar blijven.
8. **`diagnosis_incomplete`?** Niet-terminale capture of ontbrekende verplichte onderdelen.
