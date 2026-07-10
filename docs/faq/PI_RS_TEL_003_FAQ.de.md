# PI-RS-TEL-003 FAQ (DE)

Lab preview only — kein Produktivsend.

## Was wird verifiziert?

Der Rescue-Stick-Preview-Payload wird gegen CSE **0.1.0-lab2** und Diagnostics **DIAG-LAB-003** geprüft: Validate API akzeptiert, Findings Preview erzeugt Findings — alles `preview_only`.

## Warum kein Produktivsend?

PI-RS-TEL-003 ist Cross-Repo-Verifikation, kein Live-Betrieb. `production_ready=false`, `external_calls=false` im Default.

## Warum sind Plesk/DNS/Mail/SSL/Backup unknown?

Der Stick hat keine Server-Inventardaten. Unknown/preview_only ist zulässig und erzeugt DIAG-LAB-003 Preview-Findings.

## Bleibt die Offline Queue erhalten?

Ja. PI-RS-TEL-002 Offline-Queue-Preview bleibt kompatibel.

## Nächster Schritt?

PI-RS-BUILD-001 oder PI-RS-LIVE-001 mit explizitem Operator-Consent.
