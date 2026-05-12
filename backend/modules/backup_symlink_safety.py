"""
Symlink-Ziele in Tar-Archiven: relative Ziele dürfen nach Auflösung nicht aus dem Wurzelverzeichnis entweichen.
Absolute Ziele werden zugelassen (typisch unter /etc), bergen aber weiterhin semantisches Risiko beim späteren Folgen.
"""

from __future__ import annotations

import posixpath
from pathlib import Path


def tar_symlink_linkname_allowed(linkname: str, member_arcname: str, root: Path) -> bool:
    if not linkname or "\x00" in linkname:
        return False
    if posixpath.isabs(linkname):
        return True
    # resolve() hier nur für ..-Normalisierung und Pfadflucht-Erkennung (nicht für Archiv-Symlink-Leafs).
    root_r = root.resolve()
    mdir = posixpath.dirname(posixpath.normpath(member_arcname.lstrip("./")))
    parent = (root_r / mdir).resolve()
    try:
        dest = (parent / linkname).resolve()
        dest.relative_to(root_r)
        return True
    except ValueError:
        return False


__all__ = ["tar_symlink_linkname_allowed"]
