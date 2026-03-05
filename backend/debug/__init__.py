"""
PI-Installer Debug & Observability – Core-Infrastruktur (kein UI).
Schema v1: debug.config.yaml, JSON-Lines-Logging, Run-ID, Scopes, Rotating Logs, Redaction, Support-Bundle.
"""

from .config import load_debug_config, get_effective_config, get_effective_module_config, get_effective_step_config
from .redaction import redact_value, redact_recursive
from .logger import (
    init_debug,
    get_logger,
    set_run_id,
    get_run_id,
    should_log,
    should_verbose_dump_on_error,
    run_start,
    run_end,
    write_event,
)
from .support_bundle import create_support_bundle

__all__ = [
    "load_debug_config",
    "get_effective_config",
    "get_effective_module_config",
    "get_effective_step_config",
    "redact_value",
    "redact_recursive",
    "init_debug",
    "get_logger",
    "set_run_id",
    "get_run_id",
    "should_log",
    "should_verbose_dump_on_error",
    "run_start",
    "run_end",
    "write_event",
    "create_support_bundle",
]
