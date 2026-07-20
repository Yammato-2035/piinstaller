# 11 – Repair Path Decision

## Für das TUI-Menüproblem: weiterhin **E**

Keine belastbare H7/FD-Bestätigung ohne finalisierte Diagnose-Evidence.

## Separater, klarer Implementierungsbedarf (nicht jetzt umsetzen)

**Evidence-Root:** `resolve_evidence_root` soll SETUP_LOGS zuverlässig mounten/finden (`allow_mount=True` oder Warten auf Resolver), bevor nach `/run/setuphelfer/tui-input-diagnostics` gefallen wird; optional Early-Flush der Meta-Dateien.

Betroffene Datei (künftig): `backend/core/rescue_tui_input_diagnostic.py` (+ ggf. Resolver).

## Operator-Zwischenweg ohne Code

Falls der Assistent auf tty2 bedienbar ist: Lauf vollständig finalisieren; vor Poweroff muss der Assistent Erfolg melden. Ohne Code-Fix bleibt das Risiko des `/run`-Fallbacks bestehen.
