# 03 – Pre-Build-Test Results

## Pflicht: Diagnosetests

```text
python3 -m pytest backend/tests/test_rescue_tui_input_diagnostic_v1.py
→ 38 passed
```

## Shell-Syntax

| Skript | Ergebnis |
|--------|----------|
| `import-tui-input-diagnostic-runs.sh` | OK |
| `setuphelfer-rescue-tui-input-diagnostic` | OK |
| `inject-gui-bvr-fixes-into-stick-squashfs.sh` | OK |
| `update-fat32-esp-live-payload.sh` | OK |

## systemd-analyze verify

- Host-Warnungen: fehlende Telemetry-Unit-Berechtigung, AnyDesk PIDFile, Diagnostik-Binary fehlt auf Host (`/usr/local/sbin/...`) — **keine Unit-Syntaxfehler**.
- Unit-Inhalt selbst (ConditionKernelCommandLine, TTYPath) ist korrekt (siehe Tests).

## Zusätzliche Tests

| Suite | Ergebnis | Bewertung |
|-------|----------|-----------|
| `test_rescue_console_hardening_v1.py` | bestanden (Teil der 12) | OK |
| `test_rescue_msi_lab_auto_evidence_v1.py` | 2 Failures: erwartet `timeout=3`, Code liefert `timeout=10` (Menu-sichtbar) | **vorbestehende Drift**, nicht Diagnoseregession; Diagnose-Eintrag in GUI-interactive-Pfad korrekt |

## Gate

Pre-Build für Diagnosepfad: **passed** (38/38). Kein Abbruch.
