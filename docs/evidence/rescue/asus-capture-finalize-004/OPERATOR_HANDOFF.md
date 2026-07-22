# Operator-Handoff — PI-RS-ASUS-CAPTURE-FINALIZE-004

## Gerät
ASUS ROG Strix G513QM (Gabriel), Profil `asus_rog_gabriel`.

## Stick
Ultra-Line mit Payload **1.10.2.2** (nach Update).

## Ablauf
1. Netzteil anschließen.
2. Stick booten → GRUB **ASUS Hardwarediagnose (nur Lesen)**.
3. Bestätigungsphrase eingeben.
4. Phasen abwarten (SMART, Windows-Logs, Prüfsummen).
5. Meldung: Diagnose abgeschlossen – Stick kann nach dem Herunterfahren entfernt werden.
6. Kontrolliert herunterfahren, Stick zurückgeben.

## Import
Nur exakte Boot-/Run-ID mit `terminal=true` und Marker. Kein MSI-Fallback.
