# 10 – Hypothesis Decision

| Hypothese | Dafür | Dagegen | Fehlende Evidence | Bewertung |
|-----------|-------|---------|-------------------|-----------|
| H4 Terminalzustand | — | — | kein tty-State-Dump | low (ungeprüft) |
| H6 Kernel/Input | — | Payload/Stick OK | kein tty2/evdev-Test | low (ungeprüft) |
| H7 newt/Redraw | historische High-CPU-Hinweise | kein Nachweis Events+FD+kein Konkurrent | gesamter Diagnoselauf | medium (weiterhin plausibel, **unbestätigt**) |
| FD-Mismatch | — | — | keine FDs | low (ungeprüft) |
| TTY-Konkurrenz | GUI startete kurz | Owner später tui | keine FD-Liste | low |
| Payload-Drift | — | 1.10.0.59 + Hashes AUTO-002 | — | **low** |

## Führende Hypothese

```text
leading_hypothesis=undetermined
confidence=none
recommended_action=additional_targeted_diagnostic
```

Ursache dieses Auftragsabschlusses: **Diagnoseeintrag nicht gestartet**, nicht ein neuer Root-Cause.
