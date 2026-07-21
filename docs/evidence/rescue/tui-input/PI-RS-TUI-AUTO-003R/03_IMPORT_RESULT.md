# 03 – Import Result

## Befehl
```bash
bash scripts/rescue/import-tui-input-diagnostic-runs.sh
```

## Ergebnis
```text
status=blocked reason=setup_logs_diag_root_missing
exit=2
```

## Bedeutung
Es existiert **kein** Verzeichnis `SETUP_LOGS/tui-input-diagnostics/` auf dem Stick.
Damit gibt es **keinen** importierbaren Run (weder final noch `.partial`).

## Was trotzdem gesichert wurde
Incidental Boot-/Session-Artefakte unter:
`docs/evidence/rescue/tui-input/PI-RS-TUI-AUTO-003R/incidental/`

Das ersetzt **nicht** die formale Diagnose-Evidence (`01-…`–`18-…`, Manifest, SHA256).
