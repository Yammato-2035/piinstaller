# Beta-Registrierung FAQ (DE)

## Was wird erfasst?
Pseudonyme Stick-ID, Geräte-Fingerprint (gehasht), redigierte Hardware-/Fehlerzusammenfassung nach ausdrücklicher Einwilligung.

## Was wird nicht erfasst?
Keine Ausweisdaten, keine Klartext-E-Mail in Telemetrie, keine IP/MAC/Seriennummern, keine Dateilisten.

## Warum verifizierte Sticks?
Damit nur registrierte Betatest-Sticks Daten senden können — Schutz vor Spam und Missbrauch.

## Warum neuer Rechner freigegeben werden muss?
Jeder neue Zielrechner erhält `pending` bis zur Portal-Freigabe — verhindert Daten von fremden Geräten.

## Was passiert ohne Betatestvereinbarung?
Telemetrie landet in **Quarantine** (max. 14 Tage), kein Export an den Diagnostikserver.

## Warum keine Ausweisdaten?
Datensparsamkeit und DSGVO — MFA bevorzugt per Passkey/TOTP.

## Warum WordPress nicht Root-of-Trust?
Registrierung, MFA und Stick-Keys laufen ausschließlich über den FastAPI Beta-Service.
