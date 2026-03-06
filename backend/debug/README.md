# backend/debug – Datenmodell & Config

Kurzüberblick für Nutzung im Backend.

## Debug aktivieren

- **System-Config (empfohlen):** `/etc/pi-installer/debug.config.yaml` anlegen (siehe `config_schema.md`).  
  Beispiel: `global.enabled: true`, `global.level: INFO`, `global.sink.file.path: ""` (Auto: /var/log/piinstaller oder Fallback ~/.cache/piinstaller/logs).
- **ENV:** `PIINSTALLER_DEBUG_ENABLED=1`, `PIINSTALLER_DEBUG_LEVEL=DEBUG`, `PIINSTALLER_DEBUG_PATH=/pfad/zur/datei.jsonl` (optional).

## Wo liegen die Logs?

- **Bevorzugt:** `/var/log/piinstaller/piinstaller.debug.jsonl` (falls Verzeichnis schreibbar, z.B. als root).
- **Fallback:** `~/.cache/piinstaller/logs/piinstaller.debug.jsonl` (wenn /var/log/piinstaller nicht beschreibbar).

Rotation nach Größe (config `global.rotate`); rotierte Dateien: `piinstaller.debug.1.jsonl`, `.2.jsonl`, …

## Support-Bundle erstellen

```bash
cd backend && python3 -m debug.cli support-bundle
# Optional: --out-dir /tmp --max-log-lines 2000
# Optional: --no-include-system-logs / --no-include-debug-logs / --no-include-snapshot
```

Oder aus dem Repo-Root:

```bash
./scripts/support-bundle.sh
./scripts/support-bundle.sh /tmp
```

Bundle-Name: `piinstaller-support-<YYYYMMDD-HHMMSS>-<run_id>.zip`.  
Inhalt (alles redigiert): Debug-Logs, System-Logs (/var/log/pi-installer, begrenzt), `system_snapshot.json`, `debug.config.effective.yaml`, `manifest.json`.

## Module/Steps freischalten (Scopes)

In `/etc/pi-installer/debug.config.yaml` (oder defaults):

```yaml
scopes:
  modules:
    storage_nvme:
      enabled: true
      level: DEBUG
      steps:
        detect:
          level: DEBUG
        apply_boot_config:
          level: INFO
    network:
      enabled: true
      level: DEBUG
      steps:
        detect:
          level: DEBUG
```

Beispiel: Nur `storage_nvme.detect` auf DEBUG:

```yaml
scopes:
  modules:
    storage_nvme:
      enabled: true
      level: INFO
      steps:
        detect:
          level: DEBUG
```

## Config

- **Defaults:** `backend/debug/defaults.yaml` (Schema v1)
- **System:** `/etc/pi-installer/debug.config.yaml` (optional)
- **ENV:** `PIINSTALLER_DEBUG_ENABLED`, `PIINSTALLER_DEBUG_LEVEL`, `PIINSTALLER_DEBUG_PATH`

Effective Config: `defaults` → `system` → ENV (siehe `config_schema.md`).

## API (config.py)

- `load_defaults()` – lädt defaults.yaml (Exception wenn fehlt)
- `load_system_config()` – lädt System-Config (leeres dict wenn fehlt)
- `apply_env_overrides(cfg)` – ENV in-place
- `deep_merge(a, b)` – rekursiv
- `load_effective_config()` – einmalig ohne Cache
- `get_effective_config_cached(force_reload=False)` – gecachte effective config
- `dump_effective_config(path)` – schreibt effective Config als YAML (z.B. für Support-Bundle)

## Pfade (paths.py)

- `DEFAULT_DEBUG_LOG_PATH` = `/var/log/piinstaller/piinstaller.debug.jsonl`
- `FALLBACK_DEBUG_LOG_PATH` = `~/.cache/piinstaller/logs/piinstaller.debug.jsonl`
- `resolve_debug_log_path(preferred_path)` – bevorzugter Pfad oder Default/Fallback je nach Schreibrechten

## Redaction (redaction.py)

- `compile_patterns(patterns)` – regex kompilieren (einmal, oft anwenden)
- `redact_string(s, patterns)` – String redigieren
- `redact_value(obj, patterns)` – rekursiv dict/list/tuple/set/str
- `get_redact_patterns()` / `get_compiled_redact_patterns()` – aus Config

## Logger (logger.py)

- `init_debug(run_id=None)` – run_id setzen, Log-Pfad aus Config/paths
- `get_run_id()`, `get_logger(module_id, step_id=None)`, `should_log(level, module_id, step_id)`
- `write_event(event_dict)` – JSONL-Zeile (Redaktion, Rotation vor Write), wirft nie
- ModuleLogger: `step_start`, `step_end`, `decision`, `apply_attempt`, `apply_noop`, `apply_success`, `apply_failed`, `error`
- App-Name: `pi-installer-backend`; context: host, user, pid

## Context (context.py) / Levels (levels.py) / Rotation (rotate.py)

- ContextVars: `request_id`, `module_id`, `step_id`; `bind_request_id`/`reset_request_id` für Middleware
- Levels: DEBUG=10, INFO=20, WARN=30, ERROR=40; `should_log_level(event_level, effective_level)`
- `rotate.rotate_if_needed(path, max_size_bytes, max_files)` – Shift base→.1, .n→.n+1

## Middleware (middleware.py)

- `debug_request_id_middleware` – setzt request_id pro Request, optional X-Request-ID im Response

## Selftest & Tests

Tests schreiben **nicht** nach /var/log; nutzen temp dirs und ggf. `PIINSTALLER_DEBUG_PATH`.

```bash
cd backend && python -m debug._selftest
```
Prüft INFO-Event, Redaction, Rotation (nur temp dir).

```bash
cd backend && python -m unittest tests.test_debug tests.test_debug_instrumentation tests.test_debug_logger -v
```
Unit-Tests: Config-Merge, should_log, Redaction, Rotation, Support-Bundle, instrumentierte Module (storage_nvme, network, apply_boot_config).
