"""Root-Full-Backup: Tar-Mitglieder ``.`` / ``./…`` müssen in Verify/Analyse erlaubt bleiben; ``..`` weiter blockiert."""

from __future__ import annotations

import io
import tarfile
import tempfile
import unittest
from pathlib import Path

from modules.backup_verify import _is_safe_member_name


class TestFullbackupTarMemberPathV1(unittest.TestCase):
    def test_is_safe_member_name_allows_dot_and_dot_slash(self) -> None:
        self.assertTrue(_is_safe_member_name("."))
        self.assertTrue(_is_safe_member_name("./"))
        self.assertTrue(_is_safe_member_name("./etc/passwd"))
        self.assertTrue(_is_safe_member_name("home/user/file.txt"))

    def test_is_safe_member_name_blocks_traversal(self) -> None:
        self.assertFalse(_is_safe_member_name("../etc/passwd"))
        self.assertFalse(_is_safe_member_name("./../bad"))
        self.assertFalse(_is_safe_member_name("a/../../b"))

    def test_is_safe_member_name_blocks_absolute(self) -> None:
        self.assertFalse(_is_safe_member_name("/etc/passwd"))

    def test_analyze_tar_members_allows_root_placeholder_blocks_dotdot(self) -> None:
        from app import _analyze_tar_members

        with tempfile.TemporaryDirectory() as td:
            path = str(Path(td) / "sample.tar.gz")
            with tarfile.open(path, "w:gz") as tf:
                d = tarfile.TarInfo(".")
                d.type = tarfile.DIRTYPE
                d.mode = 0o755
                tf.addfile(d)

                f = tarfile.TarInfo("./hello.txt")
                f.type = tarfile.REGTYPE
                f.size = 3
                tf.addfile(f, io.BytesIO(b"hey"))

                bad = tarfile.TarInfo("../escape.txt")
                bad.type = tarfile.REGTYPE
                bad.size = 0
                tf.addfile(bad, io.BytesIO(b""))

            info = _analyze_tar_members(path)
            self.assertNotIn(".", info["blocked_entries"])
            self.assertNotIn("./hello.txt", info["blocked_entries"])
            self.assertIn("../escape.txt", info["blocked_entries"])


if __name__ == "__main__":
    unittest.main()
