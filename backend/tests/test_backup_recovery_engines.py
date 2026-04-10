"""
Backup/Recovery-Engines: Simulation Zerstörung + Restore nur in temporären Pfaden.
Lauf: cd backend && python -m unittest tests.test_backup_recovery_engines -v
"""

from __future__ import annotations

import unittest
from pathlib import Path

import sys

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.block_device_allowlist import is_allowed_block_device
from modules.backup_crypto import decrypt_bytes, encrypt_bytes, generate_key
from modules.backup_engine import create_file_backup, create_manifest
from modules.backup_verify import verify_basic, verify_deep
from modules.restore_engine import restore_files


class TestAllowlist(unittest.TestCase):
    def test_rejects_random_and_partitions(self):
        self.assertFalse(is_allowed_block_device("/dev/random"))
        self.assertFalse(is_allowed_block_device("/dev/null"))
        self.assertFalse(is_allowed_block_device("/dev/sda1"))
        self.assertTrue(is_allowed_block_device("/dev/sda"))
        self.assertTrue(is_allowed_block_device("/dev/nvme0n1"))
        self.assertTrue(is_allowed_block_device("/dev/mmcblk0"))


class TestBackupRoundtrip(unittest.TestCase):
    def test_simulate_destroy_and_restore(self):
        """Fake-System in tmp: Datei sichern, löschen, aus Archiv wiederherstellen."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            sysdir = base / "fake_root" / "etc"
            sysdir.mkdir(parents=True)
            f = sysdir / "important.cfg"
            f.write_text("secret=42\n", encoding="utf-8")

            arch = base / "bak.tar.gz"
            res = create_file_backup(
                [f],
                archive_path=arch,
                allowed_source_prefixes=(base,),
                allowed_output_prefixes=(base,),
            )
            self.assertTrue(res.ok, res.detail)
            f.unlink()
            self.assertFalse(f.is_file())

            restore_dir = base / "restored"
            rr = restore_files(
                arch,
                restore_dir,
                allowed_target_prefixes=(base,),
                dry_run=False,
            )
            self.assertTrue(rr[0], rr[2])
            # extractall legt MANIFEST + Dateiname ab
            found = list(restore_dir.rglob("important.cfg"))
            self.assertTrue(found, "restored file missing")
            self.assertEqual(found[0].read_text(encoding="utf-8"), "secret=42\n")

    def test_verify_basic_and_deep(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            f = base / "a.txt"
            f.write_text("x", encoding="utf-8")
            arch = base / "b.tar.gz"
            res = create_file_backup(
                [f],
                archive_path=arch,
                allowed_source_prefixes=(base,),
                allowed_output_prefixes=(base,),
            )
            self.assertTrue(res.ok)
            vb, k1, _ = verify_basic(arch)
            self.assertTrue(vb, k1)
            vd, k2, det = verify_deep(arch, extract_root=base, try_loop_mount_image=False)
            self.assertTrue(vd, (k2, det))


class TestCrypto(unittest.TestCase):
    def test_aes_roundtrip_no_key_in_ciphertext(self):
        key = generate_key()
        pt = b"payload"
        ct = encrypt_bytes(pt, key)
        self.assertNotIn(key, ct)
        self.assertEqual(decrypt_bytes(ct, key), pt)


class TestManifest(unittest.TestCase):
    def test_manifest_hashes(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "x.bin"
            p.write_bytes(b"abc")
            m = create_manifest([p], partition_device=None)
            self.assertEqual(m["files"][0]["sha256"], "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")


class TestDdSmoke(unittest.TestCase):
    def test_create_image_backup_mocked(self):
        from subprocess import CompletedProcess

        from modules.backup_engine import create_image_backup
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.img"

            def fake_run(argv, **kwargs):
                for part in argv:
                    if isinstance(part, str) and part.startswith("of="):
                        Path(part.split("=", 1)[1]).write_bytes(b"\0")
                return CompletedProcess(argv, 0, "", "")

            r = create_image_backup(
                "/dev/sda",
                out,
                allowed_output_prefixes=(Path(tmp),),
                runner=fake_run,
            )
            self.assertTrue(r.ok)


if __name__ == "__main__":
    unittest.main()
