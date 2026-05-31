#!/usr/bin/env python3
"""Parse QEMU serial log for SETUPHELFER_QEMU_SMOKE_RESULT_JSON markers."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

MARKER = re.compile(
    r"SETUPHELFER_QEMU_SMOKE_RESULT_JSON_BEGIN\s+(\{.*?\})\s+SETUPHELFER_QEMU_SMOKE_RESULT_JSON_END",
    re.DOTALL,
)


def parse_serial_log(path: Path) -> dict | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    matches = MARKER.findall(text)
    if not matches:
        return None
    try:
        return json.loads(matches[-1])
    except json.JSONDecodeError:
        return {"parse_error": True, "raw_tail": matches[-1][:500]}


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: parse-qemu-serial-smoke-result.py SERIAL_LOG [OUT_JSON]", file=sys.stderr)
        return 2
    serial = Path(sys.argv[1])
    result = parse_serial_log(serial)
    if result is None:
        print(json.dumps({"found": False, "serial_log": str(serial)}))
        return 1
    out = json.dumps(result, indent=2, ensure_ascii=False)
    if len(sys.argv) >= 3:
        Path(sys.argv[2]).write_text(out + "\n", encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
