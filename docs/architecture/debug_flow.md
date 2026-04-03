# Debugfluss – PI-Installer

_Phase 4 – Strukturelle Systemvereinfachung_

## 1. Ziel

Ein einheitlich angebundenes, nachvollziehbares Debugsystem. Alte und neue Log-Welten sind fachlich abgegrenzt.

---

## 2. Zentrale Einstiegsstellen

### Neues Debugsystem (backend/debug/)

| Komponente | Datei | Zweck |
|------------|-------|-------|
| Config | `debug/config.py` | Layering defaults → system → ENV |
| Logger | `debug/logger.py` | `init_debug`, `get_logger`, `run_start`, `run_end` |
| Support-Bundle | `debug/support_bundle.py` | ZIP mit Logs, Snapshot, Sanitized |
| Pfade | `debug/paths.py` | Log-Pfad (/var/log/piinstaller oder ~/.cache) |

### Verwendung in app.py

```python
from debug.logger import init_debug, run_start, run_end, get_logger, ...
```

- `init_debug()` im Startup
- `run_start()` / `run_end()` für Request-Lifecycle
- `get_logger(module, step)` für fachliche Instrumentierung

---

## 3. Modulabdeckung

| Modul/Bereich | Debugging | Anbindung |
|---------------|-----------|-----------|
| backend/app.py | ja | init_debug, run_start, run_end, get_logger |
| backend/modules/raspberry_pi_config.py | ja | get_logger |
| Frontend | teilweise | primär console.*, kein zentraler Kanal |
| Setup-Seiten | teilweise | viele Ad-hoc-Pfade |
| Scripts | nein | echo, journalctl, dmesg |

---

## 4. Erlaubte Debugpfade

- Aufruf von `get_logger(module_id, step_id)` für strukturierte Logging-Events
- Nutzung von `run_start` / `run_end` für Request-Tracking
- Support-Bundle über `debug/support_bundle.py`
- ENV: `PIINSTALLER_DEBUG_ENABLED`, `PIINSTALLER_DEBUG_LEVEL`, `PIINSTALLER_DEBUG_PATH`

---

## 5. Verbotene / Altpfade

| Altpfad | Problem | Ersatz |
|---------|---------|--------|
| `print()` im Produktivpfad | Unstrukturiert | `get_logger()` oder Standard-Logging |
| `console.*` im Frontend ohne Guard | Rauschen, ggf. sensible Daten | Dev-Only-Guard oder Backend-Korrelation |
| Zwei Logging-Welten parallel | File-Logger + Debug-Logger | Fachlich abgrenzen; Debug für strukturierte Events |

---

## 6. Diagnose-Companion (Phase 1)

Strukturierte **Interpretation** von Fehlerkontexten für die UI: siehe [`diagnose_companion.md`](diagnose_companion.md) und `POST /api/diagnosis/interpret`. `request_id` kann im Interpret-Request mitgegeben werden, um später mit JSONL-Events zu korrelieren.

---

## 7. Restunsicherheiten

- Frontend: Kein einheitlicher Debugkanal auf Backend-Niveau
- SettingsPage Logs-Tab: Zeigt klassische Backend-Logs, nicht JSONL-Debug
- Support-Bundle: `_redact_text_line_by_line()` / `compile_patterns()` – Import prüfen (G-002)
