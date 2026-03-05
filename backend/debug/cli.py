"""
CLI für Debug: support-bundle.
Aufruf: python -m debug.cli support-bundle (aus backend/) oder piinstaller support-bundle.
"""

import sys
from pathlib import Path

# Stell sicher, dass backend im Pfad ist (Aufruf aus Repo-Root)
_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend.parent))

from debug.support_bundle import create_support_bundle
from debug.logger import set_run_id


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] != "support-bundle":
        print("Usage: python -m debug.cli support-bundle [output_dir]", file=sys.stderr)
        return 1
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    set_run_id()
    try:
        zip_path = create_support_bundle(output_dir=output_dir)
        print(zip_path)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
