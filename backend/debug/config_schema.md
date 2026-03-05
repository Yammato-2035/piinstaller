# Debug-Config Schema v1

## System-Config

- **Pfad:** `/etc/pi-installer/debug.config.yaml`
- Optional; fehlt die Datei, gelten nur Defaults + ENV.

## Layering (Effective Config)

1. **Defaults:** `backend/debug/defaults.yaml` (muss existieren)
2. **System:** `/etc/pi-installer/debug.config.yaml` (optional)
3. **ENV:** `PIINSTALLER_DEBUG_ENABLED`, `PIINSTALLER_DEBUG_LEVEL`, `PIINSTALLER_DEBUG_PATH`

Merge: `deep_merge(defaults, system)` → dann `apply_env_overrides(cfg)`.

## ENV-Overrides

| Variable | Werte | Anmerkung |
|----------|--------|-----------|
| `PIINSTALLER_DEBUG_ENABLED` | 1/0, true/false, yes/no (case-insensitive) | überschreibt `global.enabled` |
| `PIINSTALLER_DEBUG_LEVEL` | DEBUG, INFO, WARN, ERROR | sonst ValueError |
| `PIINSTALLER_DEBUG_PATH` | Dateipfad | überschreibt `global.sink.file.path` |

## Beispiel defaults.yaml (Ausschnitt)

```yaml
global:
  enabled: true
  level: INFO
  sink:
    file:
      path: /var/log/piinstaller/piinstaller.debug.jsonl
  rotate:
    max_files: 10
    max_size_mb: 5
  retention:
    max_age_days: 7
  privacy:
    sanitize: true
    redact_patterns: ["password\\s*[=:]\\s*\\S+", ...]
  export:
    enabled: true
    output_dir: /tmp/piinstaller-support
scopes:
  modules: {}
```
