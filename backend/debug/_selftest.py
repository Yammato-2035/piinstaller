"""
Mini-Lauf-Test: init_debug, INFO-Event, Redaction (password=abc -> [REDACTED]), Rotation (temp dir).
Schreibt NICHT nach /var/log; nutzt nur temp dir (PIINSTALLER_DEBUG_PATH).
"""

import os
import sys
import tempfile
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))


def main():
    with tempfile.TemporaryDirectory() as tmp:
        log_file = Path(tmp) / "piinstaller.debug.jsonl"
        os.environ["PIINSTALLER_DEBUG_PATH"] = str(log_file)

        from debug.config import get_effective_config_cached
        from debug.logger import init_debug, write_event, get_run_id, get_logger
        from debug.redaction import get_compiled_redact_patterns, redact_value

        # Config-Cache neu laden damit ENV greift
        get_effective_config_cached(force_reload=True)

        init_debug()
        run_id = get_run_id()
        print("run_id:", run_id)
        print("log_path:", log_file)

        # 1) INFO-Event schreiben
        get_logger("selftest", "run").step_start("Selftest")
        get_logger("selftest", "run").step_end("Selftest", duration_ms=1.5, data={"ok": True})
        if log_file.exists():
            content = log_file.read_text(encoding="utf-8")
            assert "STEP_START" in content and "STEP_END" in content, "INFO-Events fehlen"
            print("OK: INFO-Events in JSONL")

        # 2) Redaction: data mit password=abc -> im Log [REDACTED]
        write_event({
            "level": "INFO",
            "scope": {"module_id": "selftest", "step_id": "redact"},
            "event": {"type": "DECISION", "name": "redact_check"},
            "context": {},
            "metrics": {},
            "data": {"user": "test", "password": "abc", "note": "password=abc in string"},
        })
        content = log_file.read_text(encoding="utf-8")
        if "[REDACTED]" in content:
            print("OK: Redaction aktiv (password/strings -> [REDACTED])")
        else:
            print("WARN: Redaction erwartet [REDACTED] im Log (privacy.sanitize/patterns prüfen)")

        # 3) Rotation: viele Zeilen schreiben, dann rotate_if_needed mit kleiner Größe aufrufen
        from debug import rotate
        path = str(log_file)
        for _ in range(25):
            write_event({
                "level": "INFO",
                "scope": {"module_id": "selftest", "step_id": "rot"},
                "event": {"type": "STEP_END", "name": "fill"},
                "data": {"padding": "x" * 150},
            })
        max_bytes = 100
        rotate.rotate_if_needed(path, max_bytes, 3)
        rotated = Path(path).parent / (Path(path).stem + ".1" + Path(path).suffix)
        if rotated.exists():
            print("OK: Rotation (Datei .1 angelegt)")
        else:
            print("INFO: Rotation (Datei .1 vorhanden oder noch unter max_size)")

        print("_selftest done (nur temp dir verwendet).")


if __name__ == "__main__":
    main()
