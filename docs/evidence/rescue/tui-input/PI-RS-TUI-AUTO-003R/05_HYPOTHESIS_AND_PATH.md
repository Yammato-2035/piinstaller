# 05 – Hypothesis and Path

## Führende Hypothese
**undetermined**

Begründung: Diagnoseprozess startete, aber **keine** persistente Run-Evidence. Ohne `18-final-result.json` / Manifest / SHA256 keine bestätigte Root-Cause-Entscheidung aus dem Automatikpfad.

## Operator-Hinweis (informell, nicht bestätigt)
Tastatur reagiert → frühere Hypothese „Eingabe tot“ ist **geschwächt**, aber nicht formal widerlegt/bestätigt.

## Primärer Pfad
**E – weitere Diagnose / Produktänderung**, aber **nicht** als weiterer manueller Tasten-Test.

Empfohlener nächster Auftrag (außerhalb dieses STRICT-MODE-Tickets):
1. **Non-interactive auto-finalize** der TUI-Input-Diagnose (Timeout → Snapshot → Persistenz → optional Auto-Shutdown), ohne Operator-Choreografie.
2. Optional: Poweroff-/Shutdown-Pfad im Diagnosemodus klären (TUI „Ausschalten“ ist absichtlich gesperrt).

## Explizit nicht gewählt
- A/B/C/D als confirmed root cause
- Code-Fix / Build / USB-Write in diesem Ticket
