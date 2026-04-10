"""
Allowlist für Blockgeräte (Worst-Case-Restore): nur explizit erlaubte Muster.
Verhindert /dev/random, Partitionen als „Whole-Disk“-Zielfehler wo ungeeignet, etc.
"""

from __future__ import annotations

import re
from pathlib import Path

# Whole-disk Muster: /dev/sda … /dev/sdz (keine Partition sda1)
_RE_SD_WHOLE = re.compile(r"^/dev/sd[a-z]$")
# NVMe-Namespace: /dev/nvme0n1 (keine nvme0n1p1)
_RE_NVME_WHOLE = re.compile(r"^/dev/nvme[0-9]+n[0-9]+$")
# eMMC/SD-Karte ganze Gerät (optional, typisch Raspberry Pi)
_RE_MMC_WHOLE = re.compile(r"^/dev/mmcblk[0-9]+$")


def normalize_block_device(path: str | Path) -> str:
    """Gibt kanonischen String zurück (resolve nur wenn Path existiert)."""
    p = Path(path)
    try:
        if p.exists():
            return str(p.resolve())
    except OSError:
        pass
    return str(p)


def is_allowed_block_device(path: str | Path) -> bool:
    """True nur für explizit erlaubte Whole-Disk-Geräte."""
    s = normalize_block_device(path)
    if _RE_SD_WHOLE.match(s):
        return True
    if _RE_NVME_WHOLE.match(s):
        return True
    if _RE_MMC_WHOLE.match(s):
        return True
    return False


def assert_allowed_block_device(path: str | Path) -> None:
    from core.backup_recovery_i18n import K_DEVICE_NOT_ALLOWED, tr

    if not is_allowed_block_device(path):
        raise ValueError(tr(K_DEVICE_NOT_ALLOWED))
