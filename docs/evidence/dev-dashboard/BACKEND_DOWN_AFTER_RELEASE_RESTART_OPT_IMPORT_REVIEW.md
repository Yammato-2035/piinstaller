# Backend Down After Release Restart — /opt Import Review (Phase 2)

**Datum:** 2026-06-03  
**Modus:** read-only, kein Service-Start

## Runtime-Python

| Prüfung | Ergebnis |
|---------|----------|
| `/opt/setuphelfer/backend/venv/bin/python3` | **vorhanden** |
| `dev_dashboard_recent_evidence.py` unter `/opt` | **present** |

## Import-Test

```
python_ok
recent_evidence_import_ok
app_import_ok
import_exit=0
```

## Pflichtbewertung

| Feld | Wert |
|------|------|
| Runtime-Python vorhanden | **yes** |
| recent_evidence importierbar | **yes** |
| app importierbar | **yes** |
| import_exit | **0** |
| **Status** | **ok** |

**Folgerung:** Kein blinder Restart wegen Code-Import nötig; Recovery über systemd Reload/Restart ausreichend.
