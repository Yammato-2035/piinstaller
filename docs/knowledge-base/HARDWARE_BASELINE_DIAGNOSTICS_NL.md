# Hardware-baselinediagnostiek

Stand: PI-RS-HW-BASELINE-DIAG-I18N-002 (Phase 16).

Talen: [Deutsch](HARDWARE_BASELINE_DIAGNOSTICS_DE.md) · [English](HARDWARE_BASELINE_DIAGNOSTICS_EN.md) · [Français](HARDWARE_BASELINE_DIAGNOSTICS_FR.md) · [Nederlands](HARDWARE_BASELINE_DIAGNOSTICS_NL.md)

## Doel

Korte, veilige risicocheck bij rescue-start voor RAM, CPU, GPU en opslag — vóór backup/restore/OS-install/GUI.

## Gecontroleerde waarden

Subsystemresultaten, verkeerslicht-severity, gate-rechten, issue-codes.

## Niet gecontroleerd

Geen langetermijngarantie, geen foutvrij-garantie, geen automatische self-/stresstests, geen driver-/firmware-installatie.

## Statusbetekenis

`no_immediate_issue_detected` / `immediate_issue_detected` / `review_required` / `test_unavailable` / `not_tested` — nooit „healthy/passed".

## Kritieke bevindingen

Rode memory-/CPU-/storage-bevindingen blokkeren restore en OS-installatie.

## Gele bevindingen

Gele bevindingen geven `review_required` en bevelen uitgebreide tests aan.

## Veilige volgende stappen

Eerst brondata redden, daarna opvallende componenten controleren; GUI alleen bij stabiele GPU.

## Grenzen

Groen ≠ foutvrij. Ontbrekende tools → grijs/`test_unavailable`, nooit nep-groen.

## Evidence

API: `/api/rescue/hardware/baseline/*`. Unittests onder `backend/tests/test_*baseline*_v1.py`.

## Privacy

Geen serienummers/MAC/IP in telemetrie. Alleen geredigeerde statussamenvattingen.

## Uitgebreide diagnose

Memtest86+, CPU-stress, GPU-renderstress, SMART-zelftest — alleen met operatorbevestiging.
