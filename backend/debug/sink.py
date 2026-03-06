"""
Rotating File-Sink: Rotation nach Größe und max_files.
Atomares Schreiben (write in temp, rename).
"""

import os
import fcntl
import threading
from pathlib import Path
from typing import Optional

from .config import load_debug_config


class RotatingFileSink:
    """
    Schreibt Zeilen in eine Datei, rotiert nach max_size_mb, behält max_files Backups.
    Thread-safe (Lock pro write).
    """

    def __init__(
        self,
        path: str,
        max_size_mb: float = 10,
        max_files: int = 5,
    ):
        self.path = Path(path)
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        self.max_files = max(1, max_files)
        self._lock = threading.Lock()

    def _ensure_dir(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write_line(self, line: str) -> None:
        """Schreibt eine Zeile (mit Newline) atomar und rotiert bei Bedarf."""
        if not line.endswith("\n"):
            line = line + "\n"
        with self._lock:
            self._ensure_dir()
            self._rotate_if_needed()
            try:
                with open(self.path, "a", encoding="utf-8") as f:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    try:
                        f.write(line)
                        f.flush()
                        os.fsync(f.fileno())
                    finally:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except (OSError, IOError):
                pass

    def _rotate_if_needed(self) -> None:
        try:
            if not self.path.exists():
                return
            if self.path.stat().st_size < self.max_size_bytes:
                return
            # Rotate: aktuell -> .1, .1 -> .2, ...; überschreitende löschen
            for i in range(self.max_files, 0, -1):
                p = self.path.parent / f"{self.path.stem}.{i}{self.path.suffix}"
                if i == self.max_files and p.exists():
                    p.unlink(missing_ok=True)
                if i == 1:
                    self.path.rename(self.path.parent / f"{self.path.stem}.1{self.path.suffix}")
                else:
                    p_prev = self.path.parent / f"{self.path.stem}.{i - 1}{self.path.suffix}"
                    if p_prev.exists():
                        p_prev.rename(p)
        except (OSError, IOError):
            pass

    def list_log_files(self, max_lines_total: Optional[int] = None) -> list:
        """
        Liste Log-Dateien (aktuell + .1, .2, ...), neueste zuerst.
        Wenn max_lines_total gesetzt, liefert (files, total_lines) nicht – nur Dateiliste.
        """
        files = []
        if self.path.exists():
            files.append(self.path)
        for i in range(1, self.max_files + 2):
            p = self.path.parent / f"{self.path.stem}.{i}{self.path.suffix}"
            if p.exists():
                files.append(p)
        # Sort by mtime desc (neueste zuerst)
        files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return files


def get_sink() -> Optional[RotatingFileSink]:
    """Erstellt Sink aus debug.config (global.sink.file, rotate). Bei leerem path wird resolve_debug_log_path(None) genutzt (Fallback ~/.cache/...)."""
    from .paths import resolve_debug_log_path
    cfg = load_debug_config()
    global_ = cfg.get("global") or {}
    sink_cfg = global_.get("sink") or {}
    file_cfg = sink_cfg.get("file") or {}
    path = (file_cfg.get("path") or "").strip()
    if not path:
        path = resolve_debug_log_path(None)
    rotate = global_.get("rotate") or {}
    return RotatingFileSink(
        path=path,
        max_size_mb=float(rotate.get("max_size_mb", 10)),
        max_files=int(rotate.get("max_files", 5)),
    )
