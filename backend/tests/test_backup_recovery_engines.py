"""
Backup/Recovery-Engines: Simulation Zerstörung + Restore nur in temporären Pfaden.
Lauf: cd backend && python -m unittest tests.test_backup_recovery_engines -v
"""

from __future__ import annotations

import io
import json
import os
import socket
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import sys

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.block_device_allowlist import is_allowed_block_device
from modules.backup_crypto import decrypt_bytes, encrypt_bytes, generate_key
from modules.backup_engine import create_file_backup, create_manifest
from modules.backup_verify import verify_basic, verify_deep
from modules.backup_symlink_safety import tar_symlink_linkname_allowed
from modules.restore_engine import restore_files


@unittest.skipUnless(os.name == "posix", "POSIX only: symlinks and unix sockets")
class TestSymlinkAndSpecialFiles(unittest.TestCase):
    def test_directory_backup_preserves_symlink_without_dereference(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            d = base / "fake_etc" / "alsa" / "conf.d"
            d.mkdir(parents=True)
            real = d / "real.conf"
            real.write_text("pcm\n", encoding="utf-8")
            link = d / "50-pipewire.conf"
            link.symlink_to("real.conf")
            arch = base / "bak.tar.gz"
            res = create_file_backup(
                [base / "fake_etc"],
                archive_path=arch,
                allowed_source_prefixes=(base,),
                allowed_output_prefixes=(base,),
            )
            self.assertTrue(res.ok, res.detail)
            sym_entries = [e for e in res.manifest.get("files", []) if e.get("type") == "symlink"]
            self.assertTrue(sym_entries, "manifest should list symlink entries")
            le = next(e for e in sym_entries if e["path"].endswith("50-pipewire.conf"))
            self.assertEqual(le.get("link_target"), "real.conf")
            with tarfile.open(arch, "r:*") as tf:
                names = {m.name: m for m in tf.getmembers()}
                m = next(x for x in names.values() if x.name.endswith("50-pipewire.conf"))
                self.assertTrue(m.issym(), "tar member must be symlink, not dereferenced file")
                self.assertEqual(m.linkname, "real.conf")

    def test_restore_roundtrip_symlink_and_verify_deep(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            d = base / "app"
            d.mkdir()
            (d / "target.txt").write_text("x", encoding="utf-8")
            (d / "alias.txt").symlink_to("target.txt")
            arch = base / "bak.tar.gz"
            res = create_file_backup(
                [d],
                archive_path=arch,
                allowed_source_prefixes=(base,),
                allowed_output_prefixes=(base,),
            )
            self.assertTrue(res.ok, res.detail)
            out = base / "rest"
            rr = restore_files(arch, out, allowed_target_prefixes=(base,), dry_run=False)
            self.assertTrue(rr[0], rr[2])
            alias = next(out.rglob("alias.txt"))
            self.assertTrue(alias.is_symlink())
            self.assertEqual(os.readlink(alias), "target.txt")
            vd, k, det = verify_deep(arch, extract_root=base, try_loop_mount_image=False)
            self.assertTrue(vd, (k, det))

    def test_unix_socket_is_skipped_and_manifest_skipped_members(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            d = base / "mix"
            d.mkdir()
            (d / "ok.txt").write_text("ok", encoding="utf-8")
            sock_path = d / "sock"
            s = socket.socket(socket.AF_UNIX)
            try:
                s.bind(str(sock_path))
            finally:
                s.close()
            arch = base / "bak.tar.gz"
            res = create_file_backup(
                [d],
                archive_path=arch,
                allowed_source_prefixes=(base,),
                allowed_output_prefixes=(base,),
            )
            self.assertTrue(res.ok, res.detail)
            skipped = res.manifest.get("skipped_members") or []
            self.assertTrue(any("sock" in str(x.get("path", "")) for x in skipped))
            rr = restore_files(arch, base / "out", allowed_target_prefixes=(base,), dry_run=False)
            self.assertTrue(rr[0], rr[2])
            found_ok = list((base / "out").rglob("ok.txt"))
            self.assertTrue(found_ok and found_ok[0].is_file())

    def test_restore_rejects_symlink_whose_relative_target_escapes_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            arch = base / "evil.tar.gz"
            with tarfile.open(arch, "w:gz") as tf:
                info = tarfile.TarInfo(name="subdir/link")
                info.type = tarfile.SYMTYPE
                info.linkname = "../../../outside-secret"
                info.mode = 0o777
                tf.addfile(info)
            rr = restore_files(arch, base / "out", allowed_target_prefixes=(base,), dry_run=False)
            self.assertFalse(rr[0])
            self.assertIn("escapes", (rr[2] or "").lower())

    def test_tar_symlink_linkname_allowed_helper(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            self.assertTrue(tar_symlink_linkname_allowed("data/file", "etc/x", root))
            self.assertFalse(tar_symlink_linkname_allowed("../../../etc/passwd", "etc/x", root))


class TestAllowlist(unittest.TestCase):
    def test_rejects_random_and_partitions(self):
        self.assertFalse(is_allowed_block_device("/dev/random"))
        self.assertFalse(is_allowed_block_device("/dev/null"))
        self.assertFalse(is_allowed_block_device("/dev/sda1"))
        self.assertTrue(is_allowed_block_device("/dev/sda"))
        self.assertTrue(is_allowed_block_device("/dev/nvme0n1"))
        self.assertTrue(is_allowed_block_device("/dev/mmcblk0"))


class TestBackupRoundtrip(unittest.TestCase):
    def test_file_backup_single_file_still_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            src = base / "src"
            src.mkdir()
            f = src / "a.txt"
            f.write_text("x", encoding="utf-8")

            arch = base / "b.tar.gz"
            res = create_file_backup(
                [f],
                archive_path=arch,
                allowed_source_prefixes=(base,),
                allowed_output_prefixes=(base,),
            )
            self.assertTrue(res.ok, res.detail)
            vb, k1, _ = verify_basic(arch)
            self.assertTrue(vb, k1)
            vd, k2, det = verify_deep(arch, extract_root=base, try_loop_mount_image=False)
            self.assertTrue(vd, (k2, det))

    def test_directory_backup_recursive_with_relative_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "fake_root"
            (root / "etc").mkdir(parents=True)
            (root / "opt" / "setuphelfer-test").mkdir(parents=True)
            (root / "home" / "volker" / "testdata").mkdir(parents=True)
            (root / "etc" / "hosts").write_text("127.0.0.1 localhost\n", encoding="utf-8")
            (root / "opt" / "setuphelfer-test" / "marker.txt").write_text("marker\n", encoding="utf-8")
            (root / "home" / "volker" / "testdata" / "file.txt").write_text("payload\n", encoding="utf-8")

            arch = base / "bak.tar.gz"
            res = create_file_backup(
                [root / "etc", root / "opt", root / "home"],
                archive_path=arch,
                allowed_source_prefixes=(base,),
                allowed_output_prefixes=(base,),
            )
            self.assertTrue(res.ok, res.detail)
            with tarfile.open(arch, "r:*") as tf:
                names = set(tf.getnames())
            self.assertTrue(any(name.endswith("/etc/hosts") for name in names))
            self.assertTrue(any(name.endswith("/opt/setuphelfer-test/marker.txt") for name in names))
            self.assertTrue(any(name.endswith("/home/volker/testdata/file.txt") for name in names))
            self.assertNotIn("hosts", names)
            self.assertNotIn("marker.txt", names)

    def test_restore_preserves_relative_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            src_root = base / "fake_root"
            (src_root / "etc").mkdir(parents=True)
            (src_root / "etc" / "important.cfg").write_text("secret=42\n", encoding="utf-8")
            arch = base / "bak.tar.gz"
            res = create_file_backup(
                [src_root / "etc"],
                archive_path=arch,
                allowed_source_prefixes=(base,),
                allowed_output_prefixes=(base,),
            )
            self.assertTrue(res.ok, res.detail)
            restore_dir = base / "restore"
            rr = restore_files(arch, restore_dir, allowed_target_prefixes=(base,), dry_run=False)
            self.assertTrue(rr[0], rr[2])
            found = list(restore_dir.rglob("important.cfg"))
            self.assertTrue(found, "restored file missing")
            self.assertEqual(found[0].read_text(encoding="utf-8"), "secret=42\n")
            self.assertFalse((restore_dir / "MANIFEST.json").exists())

    def test_overlapping_input_paths_are_deduplicated_and_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            home = base / "home"
            nested = home / "volker" / "testdata"
            nested.mkdir(parents=True)
            (nested / "file.txt").write_text("x\n", encoding="utf-8")

            arch = base / "bak.tar.gz"
            res = create_file_backup(
                [home, nested],
                archive_path=arch,
                allowed_source_prefixes=(base,),
                allowed_output_prefixes=(base,),
            )
            self.assertTrue(res.ok, res.detail)
            self.assertIn(str(nested.resolve()), res.manifest.get("skipped_inputs", []))

    def test_archive_name_collisions_are_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            p1 = base / "a.txt"
            p2 = base / "b.txt"
            p1.write_text("a\n", encoding="utf-8")
            p2.write_text("b\n", encoding="utf-8")
            arch = base / "bak.tar.gz"

            with patch("modules.backup_engine._to_archive_path", return_value="same/path.txt"):
                res = create_file_backup(
                    [p1, p2],
                    archive_path=arch,
                    allowed_source_prefixes=(base,),
                    allowed_output_prefixes=(base,),
                )
            self.assertFalse(res.ok)
            self.assertIn("collision", (res.detail or "").lower())

    def test_verify_deep_fails_on_manifest_archive_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            src = base / "src"
            src.mkdir()
            good = src / "good.txt"
            good.write_text("ok\n", encoding="utf-8")
            arch = base / "bad-manifest.tar.gz"
            res = create_file_backup(
                [good],
                archive_path=arch,
                allowed_source_prefixes=(base,),
                allowed_output_prefixes=(base,),
            )
            self.assertTrue(res.ok, res.detail)

            with tarfile.open(arch, "r:*") as tf:
                members = tf.getmembers()
                payloads: dict[str, bytes] = {}
                for m in members:
                    if m.isfile():
                        fh = tf.extractfile(m)
                        assert fh is not None
                        payloads[m.name] = fh.read()

            manifest = json.loads(payloads["MANIFEST.json"].decode("utf-8"))
            manifest["files"][0]["path"] = "missing/file.txt"
            payloads["MANIFEST.json"] = json.dumps(manifest).encode("utf-8")

            rewritten = base / "rewritten.tar.gz"
            with tarfile.open(rewritten, "w:gz") as tf:
                for m in members:
                    data = payloads.get(m.name)
                    if data is None:
                        tf.addfile(m)
                        continue
                    info = tarfile.TarInfo(name=m.name)
                    info.mode = m.mode
                    info.mtime = m.mtime
                    info.size = len(data)
                    tf.addfile(info, io.BytesIO(data))

            ok, key, detail = verify_deep(rewritten, extract_root=base, try_loop_mount_image=False)
            self.assertFalse(ok)
            self.assertEqual(key, "backup_recovery.error.checksum_mismatch")
            self.assertEqual(detail.get("file"), "missing/file.txt")

    def test_allowlist_restrictions_are_still_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            src = base / "src"
            src.mkdir()
            f = src / "a.txt"
            f.write_text("x", encoding="utf-8")
            arch = base / "b.tar.gz"

            with self.assertRaises(ValueError):
                create_file_backup(
                    [f],
                    archive_path=arch,
                    allowed_source_prefixes=(base / "other",),
                    allowed_output_prefixes=(base,),
                )

            res = create_file_backup(
                [f],
                archive_path=arch,
                allowed_source_prefixes=(base,),
                allowed_output_prefixes=(base,),
            )
            self.assertTrue(res.ok, res.detail)
            ok, key, _ = restore_files(
                arch,
                base / "restore",
                allowed_target_prefixes=(base / "not-allowed",),
                dry_run=False,
            )
            self.assertFalse(ok)
            self.assertEqual(key, "backup_recovery.error.path_not_allowed")


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
