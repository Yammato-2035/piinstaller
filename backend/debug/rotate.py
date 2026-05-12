"""
Rotation: Wenn Datei > max_size_bytes, Shift .(n) -> .(n+1), base -> .1, neue leere base.
"""

import os
from pathlib import Path
from typing import Optional


def rotate_if_needed(path: str, max_size_bytes: int, max_files: int) -> None:
    """
    Wenn base-Datei existiert und size >= max_size_bytes:
    - .(max_files-1) löschen falls vorhanden
    - .(n) -> .(n+1) für n = max_files-2 .. 1
    - base -> .1
    - base ist danach frei (neu beschreibbar).
    Robust: wenn base nicht existiert oder size < max_size_bytes -> nichts tun.
    """
    if max_files < 1:
        return
    p = Path(path).resolve()
    try:
        if not p.exists():
            return
        if p.stat().st_size < max_size_bytes:
            return
    except (OSError, IOError):
        return

    try:
        stem, suffix = p.stem, p.suffix
        parent = p.parent
        # Lösche .(max_files-1) falls vorhanden (z.B. .9 bei max_files=10)
        high = parent / f"{stem}.{max_files - 1}{suffix}"
        if high.exists():
            try:
                high.unlink()
            except (OSError, IOError):
                pass
        # Shift: .(n) -> .(n+1) für n von max_files-2 down to 1
        for n in range(max_files - 2, 0, -1):
            src = parent / f"{stem}.{n}{suffix}"
            dst = parent / f"{stem}.{n + 1}{suffix}"
            if src.exists():
                try:
                    if dst.exists():
                        dst.unlink()
                    src.rename(dst)
                except (OSError, IOError):
                    pass
        # base -> .1
        one = parent / f"{stem}.1{suffix}"
        try:
            if one.exists():
                one.unlink()
            p.rename(one)
        except (OSError, IOError):
            pass
    except (OSError, IOError):
        pass
