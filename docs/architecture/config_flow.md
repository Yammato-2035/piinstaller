# Konfigurationsfluss – PI-Installer

_Phase 4 – Strukturelle Systemvereinfachung_

## 1. Ziel

Konfiguration soll nachvollziehbar sein: eine Primärquelle, klare Defaults, definierte Überschreibungen.

---

## 2. Haupt-Konfiguration (config.json)

### Primärquelle

| Quelle | Pfad | Priorität |
|--------|------|-----------|
| System (wenn schreibbar) | `/etc/pi-installer/config.json` | 1 |
| Fallback (User) | `~/.config/pi-installer/config.json` | 2 |

### Ladepfad

1. **Startup:** `@app.on_event("startup")` → `_load_or_init_config()` in `backend/app.py`
2. **Lesen:** `CONFIG_PATH` aus `_config_path()` (REGRESSION-RISK: nur `.json`, nicht `.yaml`)
3. **Merge:** Gespeicherte Settings werden mit `_default_settings()` gemerged (shallow + nested für ui, backup, logging, network, remote)

### Struktur

- `device_id`, `created_at`, `last_seen_at`
- `system`: hostname, model, os_release, kernel
- `settings`: ui, backup, logging, network, remote

### Wichtige Dateien

| Datei | Rolle |
|-------|-------|
| `backend/app.py` | `_config_path()`, `_load_or_init_config()`, `_default_settings()` |
| `scripts/install-system.sh` | Erzeugt config.json bei Installation |
| `scripts/deploy-to-opt.sh` | Erzeugt config.json bei Deploy |

---

## 3. Debug-Konfiguration

### Primärquelle (Layering)

1. **Defaults:** `backend/debug/defaults.yaml`
2. **System:** `/etc/pi-installer/debug.config.yaml` (optional)
3. **ENV:** `PIINSTALLER_DEBUG_ENABLED`, `PIINSTALLER_DEBUG_LEVEL`, `PIINSTALLER_DEBUG_PATH`

### Ladepfad

- `backend/debug/config.py` → `load_effective_config()` / `get_effective_config_cached()`
- ENV überschreibt Dateien

### Wichtige Dateien

| Datei | Rolle |
|-------|-------|
| `backend/debug/config.py` | Layering, ENV-Parsing |
| `backend/debug/defaults.yaml` | Default-Werte |
| `backend/debug/debug.config.yaml` | Lokale Overrides (Schema-Kommentar) |

---

## 4. Bekannte Konflikte / Vermeidung

| Problem | Status | Vermeidung |
|--------|--------|------------|
| config.yaml vs. config.json | Behoben (A-03) | Runtime liest nur JSON |
| PI_INSTALLER_DEBUG_CONFIG vs. PIINSTALLER_DEBUG_* | Behoben (B-01) | ENV: PIINSTALLER_DEBUG_* |
| .env in CONFIG.md | Unklar | CONFIG.md beschreibt .env; app.py lädt sie nicht zentral – nur dokumentiert, nicht verdrahtet |

---

## 5. Typische Fehlerquellen

1. **Neue Config-Keys:** Vor Hinzufügen prüfen, ob Schlüssel bereits in `_default_settings()` oder Debug-Config existieren.
2. **YAML wieder einführen:** Nicht. Runtime bleibt bei config.json.
3. **ENV für Debug:** Nur `PIINSTALLER_DEBUG_*` nutzen, nicht `PI_INSTALLER_DEBUG_CONFIG`.
