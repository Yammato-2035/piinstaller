"""
Level-Mapping: DEBUG=10, INFO=20, WARN=30, ERROR=40. Parser + Compare.
"""

LEVEL_ORDER = {"DEBUG": 10, "INFO": 20, "WARN": 30, "WARNING": 30, "ERROR": 40}
DEFAULT_LEVEL = "INFO"


def parse_level(s):
    """Normalisiert Level-String (z.B. WARNING -> WARN)."""
    if not s or not str(s).strip():
        return DEFAULT_LEVEL
    u = str(s).strip().upper()
    if u == "WARNING":
        return "WARN"
    return u if u in LEVEL_ORDER else DEFAULT_LEVEL


def level_value(level):
    """Numerischer Wert für Vergleich (höher = schwerer)."""
    return LEVEL_ORDER.get(parse_level(level), LEVEL_ORDER[DEFAULT_LEVEL])


def should_log_level(event_level, effective_level):
    """True wenn event_level >= effective_level (numerisch)."""
    return level_value(event_level) >= level_value(effective_level)
