#!/usr/bin/env python3
"""
Erzeugt Backup/Restore-Realtest-Daten unter /tmp/setuphelfer-test/.

Aufruf (ohne Zusatzpakete):
  python3 setuphelfer/create_backup_realtest_data.py

Siehe docs/backup-restore-realtest.md Abschnitt „Testdaten – Erzeugung“.
"""
from __future__ import annotations

import io
import os
import shutil
import stat
import subprocess
import tarfile
from pathlib import Path

BASE = Path("/tmp/setuphelfer-test")
SAFE = BASE / "safe-tree"


def main() -> None:
    BASE.mkdir(parents=True, exist_ok=True)
    if SAFE.exists():
        shutil.rmtree(SAFE)
    SAFE.mkdir(parents=True)
    (SAFE / "hello.txt").write_text("setuphelfer-realtest-ok\n", encoding="utf-8")
    (SAFE / "subdir").mkdir()
    (SAFE / "subdir" / "nested.txt").write_text("nested\n", encoding="utf-8")

    # 1) Gültiges Archiv
    valid = BASE / "valid-backup.tar.gz"
    with tarfile.open(valid, "w:gz") as tf:
        tf.add(SAFE, arcname="restore-root")

    # 2) Wirklich defektes Archiv: kein gültiges gzip → tar -tzf scheitert reproduzierbar
    corrupt = BASE / "corrupt-not-gzip.tar.gz"
    corrupt.write_bytes(b"This is not a gzip stream.\x00" * 50)

    # 3a) Path traversal (../)
    evil_trav = BASE / "evil-traversal.tar.gz"
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz", format=tarfile.GNU_FORMAT) as tf:
        data = b"escape"
        ti = tarfile.TarInfo(name="../outside-traversal.txt")
        ti.size = len(data)
        ti.mtime = 1
        ti.mode = 0o644
        ti.type = tarfile.REGTYPE
        tf.addfile(ti, io.BytesIO(data))
    evil_trav.write_bytes(buf.getvalue())

    # 3b) Absoluter Pfad
    evil_abs = BASE / "evil-absolute.tar.gz"
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz", format=tarfile.GNU_FORMAT) as tf:
        data = b"abs"
        ti = tarfile.TarInfo(name="/tmp/evil-absolute-marker.txt")
        ti.size = len(data)
        ti.mtime = 1
        ti.mode = 0o644
        ti.type = tarfile.REGTYPE
        tf.addfile(ti, io.BytesIO(data))
    evil_abs.write_bytes(buf.getvalue())

    # 3c) Symlink
    evil_sym = BASE / "evil-symlink.tar.gz"
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz", format=tarfile.GNU_FORMAT) as tf:
        ti = tarfile.TarInfo(name="link-to-etc")
        ti.type = tarfile.SYMTYPE
        ti.linkname = "/etc/passwd"
        ti.mtime = 1
        ti.mode = 0o777
        tf.addfile(ti)
    evil_sym.write_bytes(buf.getvalue())

    # 3d) Hardlink (zwei Namen auf gleiche Datei-Inhalt)
    evil_hl = BASE / "evil-hardlink.tar.gz"
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz", format=tarfile.GNU_FORMAT) as tf:
        data = b"shared"
        ti1 = tarfile.TarInfo(name="first.txt")
        ti1.size = len(data)
        ti1.mtime = 1
        ti1.mode = 0o644
        ti1.type = tarfile.REGTYPE
        tf.addfile(ti1, io.BytesIO(data))
        ti2 = tarfile.TarInfo(name="second.txt")
        ti2.type = tarfile.LNKTYPE
        ti2.linkname = "first.txt"
        ti2.mtime = 1
        ti2.mode = 0o644
        tf.addfile(ti2)
    evil_hl.write_bytes(buf.getvalue())

    # 3e) FIFO (nur Standardwerkzeuge: os.mkfifo)
    fifo_dir = BASE / "fifo-build"
    if fifo_dir.exists():
        shutil.rmtree(fifo_dir)
    fifo_dir.mkdir()
    fifo_path = fifo_dir / "thepipe"
    os.mkfifo(fifo_path, mode=0o644)
    evil_fifo = BASE / "evil-fifo.tar.gz"
    with tarfile.open(evil_fifo, "w:gz") as tf:
        tf.add(fifo_path, arcname="unsafe/pipe")
    shutil.rmtree(fifo_dir)

    # Sanity: tar -tzf auf defektem Archiv muss fehlschlagen
    r = subprocess.run(
        ["tar", "-tzf", str(corrupt)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if r.returncode == 0:
        raise SystemExit("Erwartung verletzt: corrupt-not-gzip.tar.gz wurde von tar -tzf gelesen")

    print("OK – Testdaten unter", BASE)


if __name__ == "__main__":
    main()
