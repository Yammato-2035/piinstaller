"""
Redaktion: compile_patterns einmal, redact_string für Strings, redact_value rekursiv (dict/list/tuple/set/str).
"""

import re
from typing import Any, List

_compiled_cache: List[re.Pattern] = []
_cache_patterns_key: Any = None


def compile_patterns(patterns: List[str]) -> List[re.Pattern]:
    """Kompiliert pattern-Strings (regex) für schnelle Wiederverwendung. Einmal kompilieren, oft anwenden."""
    compiled = []
    for p in patterns or []:
        try:
            compiled.append(re.compile(p, re.IGNORECASE))
        except re.error:
            continue
    return compiled


def redact_string(s: str, patterns: List[Any]) -> str:
    """Wendet kompilierte oder rohe patterns auf einen String an, Ersetzung '[REDACTED]'."""
    if not isinstance(s, str) or not s:
        return s
    out = s
    for pat in patterns or []:
        try:
            if isinstance(pat, str):
                pat = re.compile(pat, re.IGNORECASE)
            out = pat.sub("[REDACTED]", out)
        except (re.error, TypeError):
            continue
    return out


def redact_value(obj: Any, patterns: List[Any]) -> Any:
    """
    Rekursiv: dict/list/tuple/set/str. Bei str -> redact_string; sonst Kopie mit redigierten Werten.
    Andere Typen (int, bool, None) unverändert.
    """
    if patterns is None:
        patterns = []
    if not patterns:
        return obj

    def _walk(o):
        if isinstance(o, str):
            return redact_string(o, patterns)
        if isinstance(o, dict):
            return {k: _walk(v) for k, v in o.items()}
        if isinstance(o, list):
            return [_walk(i) for i in o]
        if isinstance(o, tuple):
            return tuple(_walk(i) for i in o)
        if isinstance(o, set):
            return {_walk(i) for i in o}
        return o

    return _walk(obj)


def get_redact_patterns() -> List[str]:
    """Liefert konfigurierte redact_patterns aus effective config, falls privacy.sanitize."""
    try:
        from .config import get_effective_config_cached
        cfg = get_effective_config_cached()
        privacy = (cfg.get("global") or {}).get("privacy") or {}
        if not privacy.get("sanitize", True):
            return []
        return list(privacy.get("redact_patterns") or [])
    except Exception:
        return []


def get_compiled_redact_patterns() -> List[re.Pattern]:
    """Kompilierte patterns aus Config (für Performance: einmal pro Config-Load)."""
    global _compiled_cache, _cache_patterns_key
    raw = get_redact_patterns()
    key = tuple(raw) if raw else ()
    if key != _cache_patterns_key:
        _cache_patterns_key = key
        _compiled_cache = compile_patterns(raw)
    return _compiled_cache


def redact_recursive(obj: Any, patterns: List[Any]) -> Any:
    """Alias für redact_value (Rückwärtskompatibilität)."""
    return redact_value(obj, patterns)
