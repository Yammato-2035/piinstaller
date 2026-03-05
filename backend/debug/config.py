"""
Debug-Config: Layering defaults -> system -> ENV. Schema v1.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import os

try:
    import yaml
except ImportError:
    yaml = None

_SCHEMA_VERSION = 1
_SYSTEM_CONFIG_PATH = Path("/etc/pi-installer/debug.config.yaml")
_ALLOWED_LEVELS = frozenset({"DEBUG", "INFO", "WARN", "ERROR"})

_effective_config_cache: Optional[Dict[str, Any]] = None


def _defaults_path() -> Path:
    return Path(__file__).resolve().parent / "defaults.yaml"


def deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Rekursiv: dicts werden gemerged, b überschreibt a."""
    out = dict(a)
    for k, v in b.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_defaults() -> Dict[str, Any]:
    """Lädt backend/debug/defaults.yaml. Wirft bei fehlender Datei eine klare Exception."""
    p = _defaults_path()
    if not p.is_file():
        raise FileNotFoundError(f"Debug defaults fehlen: {p}")
    raw = p.read_text(encoding="utf-8")
    if yaml:
        data = yaml.safe_load(raw)
    else:
        import json
        data = json.loads(raw) if raw.strip() else None
    if not isinstance(data, dict):
        raise ValueError(f"Ungültiges Format in {p}: erwartet YAML-Mapping")
    return data


def load_system_config() -> Dict[str, Any]:
    """Lädt /etc/pi-installer/debug.config.yaml falls vorhanden. Fehlt die Datei: leeres dict."""
    if not _SYSTEM_CONFIG_PATH.is_file():
        return {}
    try:
        raw = _SYSTEM_CONFIG_PATH.read_text(encoding="utf-8")
        if yaml:
            data = yaml.safe_load(raw)
        else:
            import json
            data = json.loads(raw) if raw.strip() else {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _parse_enabled(value: str) -> bool:
    v = (value or "").strip().lower()
    if v in ("1", "true", "yes"):
        return True
    if v in ("0", "false", "no"):
        return False
    raise ValueError(f"PIINSTALLER_DEBUG_ENABLED ungültig: '{value}' (erwartet: 1/0, true/false, yes/no)")


def apply_env_overrides(cfg: Dict[str, Any]) -> None:
    """
    Überschreibt cfg in-place mit ENV:
    - PIINSTALLER_DEBUG_ENABLED: 1/0, true/false, yes/no (case-insensitive)
    - PIINSTALLER_DEBUG_LEVEL: nur DEBUG, INFO, WARN, ERROR (sonst ValueError)
    - PIINSTALLER_DEBUG_PATH: Pfad für sink.file.path
    """
    global_section = cfg.setdefault("global", {})
    sink = global_section.setdefault("sink", {}).setdefault("file", {})

    v = os.environ.get("PIINSTALLER_DEBUG_ENABLED", "").strip()
    if v:
        global_section["enabled"] = _parse_enabled(v)

    v = os.environ.get("PIINSTALLER_DEBUG_LEVEL", "").strip().upper()
    if v:
        if v not in _ALLOWED_LEVELS:
            raise ValueError(f"PIINSTALLER_DEBUG_LEVEL ungültig: '{v}' (erlaubt: {sorted(_ALLOWED_LEVELS)})")
        global_section["level"] = v

    v = os.environ.get("PIINSTALLER_DEBUG_PATH", "").strip()
    if v:
        sink["path"] = v


def load_effective_config() -> Dict[str, Any]:
    """Layering: defaults -> system -> ENV. Gibt neue dict-Instanz zurück (nicht gecacht)."""
    cfg = deep_merge(load_defaults(), load_system_config())
    apply_env_overrides(cfg)
    cfg["_schema_version"] = _SCHEMA_VERSION
    return cfg


def get_effective_config_cached(force_reload: bool = False) -> Dict[str, Any]:
    """Cached Singleton der effective config. force_reload=True ignoriert Cache."""
    global _effective_config_cache
    if _effective_config_cache is None or force_reload:
        _effective_config_cache = load_effective_config()
    return _effective_config_cache


def dump_effective_config(path: str) -> None:
    """Schreibt die effective Config als YAML nach path (für Support-Bundle später)."""
    cfg = get_effective_config_cached()
    # Keine internen Keys im Dump
    dump_cfg = {k: v for k, v in cfg.items() if not str(k).startswith("_")}
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    if yaml:
        p.write_text(yaml.dump(dump_cfg, default_flow_style=False, allow_unicode=True), encoding="utf-8")
    else:
        import json
        p.write_text(json.dumps(dump_cfg, indent=2, ensure_ascii=False), encoding="utf-8")


# Rückwärtskompatibilität für bestehende Importer (logger, sink, support_bundle, redaction)
def load_debug_config(force_reload: bool = False) -> Dict[str, Any]:
    """Alias für get_effective_config_cached."""
    return get_effective_config_cached(force_reload=force_reload)


def get_effective_config() -> Dict[str, Any]:
    """Alias für get_effective_config_cached()."""
    return get_effective_config_cached()


def get_effective_module_config(module_id: str) -> Dict[str, Any]:
    """Effektive Config für ein Modul (global + scopes.modules.<module_id>)."""
    cfg = get_effective_config_cached()
    global_ = (cfg.get("global") or {})
    modules = (cfg.get("scopes") or {}).get("modules") or {}
    mod = modules.get(module_id) or {}
    return {
        "enabled": mod.get("enabled", global_.get("enabled", True)),
        "level": mod.get("level") or global_.get("level", "INFO"),
    }


def get_effective_step_config(module_id: str, step_id: str) -> Dict[str, Any]:
    """Effektive Config für einen Step (global -> module -> step)."""
    mod_eff = get_effective_module_config(module_id)
    cfg = get_effective_config_cached()
    modules = (cfg.get("scopes") or {}).get("modules") or {}
    steps = (modules.get(module_id) or {}).get("steps") or {}
    step = steps.get(step_id) or {}
    return {
        "enabled": step.get("enabled", mod_eff["enabled"]),
        "level": step.get("level") or mod_eff["level"],
    }
