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
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

import sys

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from datetime import datetime, timezone

from core.backup_recovery_i18n import (
    K_ARCHIVE_CORRUPT,
    K_BACKUP_FAILED_MANIFEST_MISSING,
    K_BACKUP_TARGET_NOT_WRITABLE,
    K_VERIFY_INTEGRITY_FAILED,
)
from core.block_device_allowlist import is_allowed_block_device
from modules.backup_crypto import decrypt_bytes, encrypt_bytes, generate_key
from modules.backup_engine import create_file_backup, create_manifest, embed_manifest_in_tar_gz
from modules.storage_detection import (
    BackupTargetValidationError,
    assert_backup_target_dir_writable,
    classify_devices,
    validate_backup_target,
)
from modules.backup_verify import verify_basic, verify_deep
from modules.backup_symlink_safety import tar_symlink_linkname_allowed
from modules.restore_engine import restore_files

# Schreibpfad für validate_write_target (core.safe_device)
_T_SAFE = Path("/tmp/setuphelfer-test/recovery-engine-mountval")


def _lsblk_usb_sdb1_at(mount: str) -> dict:
    return {
        "blockdevices": [
            {
                "path": "/dev/sdb",
                "name": "sdb",
                "type": "disk",
                "size": "20G",
                "rm": "1",
                "ro": False,
                "tran": "usb",
                "children": [
                    {
                        "path": "/dev/sdb1",
                        "name": "sdb1",
                        "type": "part",
                        "fstype": "ext4",
                        "mountpoints": [mount],
                        "size": "20G",
                    }
                ],
            }
        ]
    }


def _lsblk_usb_sda_whole() -> dict:
    return {
        "blockdevices": [
            {
                "path": "/dev/sda",
                "name": "sda",
                "type": "disk",
                "size": "20G",
                "rm": "1",
                "ro": False,
                "tran": "usb",
                "children": [
                    {
                        "path": "/dev/sda1",
                        "name": "sda1",
                        "type": "part",
                        "fstype": "ext4",
                        "mountpoints": ["/mnt/other"],
                        "size": "20G",
                    }
                ],
            }
        ]
    }


def _wrap_fake_run_with_lsblk(inner, mount_for_lsblk: str):
    lsblk = _lsblk_usb_sdb1_at(mount_for_lsblk)

    def fake_run(argv, **kwargs):
        if argv[:2] == ["lsblk", "-J"]:
            return CompletedProcess(argv, 0, json.dumps(lsblk), "")
        return inner(argv, **kwargs)

    return fake_run


class _SkipMountValidationMixin:
    """create_file_backup-Tests unter /tmp: Mount-Sicherheitsprüfung per Mock umgehen."""

    def setUp(self) -> None:
        p = patch("modules.backup_engine.validate_backup_target")
        p.start()
        self.addCleanup(p.stop)


@unittest.skipUnless(os.name == "posix", "POSIX only: symlinks and unix sockets")
class TestSymlinkAndSpecialFiles(_SkipMountValidationMixin, unittest.TestCase):
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
            sym_entries = [e for e in (res.manifest.get("entries") or res.manifest.get("files") or []) if e.get("type") == "symlink"]
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


class TestBackupRoundtrip(_SkipMountValidationMixin, unittest.TestCase):
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

    def test_restore_skips_tar_root_dot_member(self):
        """Root-Backups (tar aus /) enthalten oft ein Mitglied ``.`` — darf Restore nicht abbrechen."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            arch = base / "rootish.tar.gz"
            hello = base / "hello.txt"
            hello.write_text("x", encoding="utf-8")
            with tarfile.open(arch, "w:gz") as tf:
                dot = tarfile.TarInfo(name=".")
                dot.type = tarfile.DIRTYPE
                dot.mode = 0o755
                tf.addfile(dot)
                tf.add(hello, arcname="hello.txt")
            out = base / "out"
            ok, key, err = restore_files(arch, out, allowed_target_prefixes=(base,), dry_run=False)
            self.assertTrue(ok, (key, err))
            self.assertTrue((out / "hello.txt").is_file())

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
            rows = manifest.get("entries") or manifest.get("files") or []
            rows[0]["path"] = "missing/file.txt"
            manifest["entries"] = rows
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
            self.assertEqual(key, K_VERIFY_INTEGRITY_FAILED)
            self.assertFalse(detail.get("valid", True))
            errs = detail.get("errors") or []
            self.assertTrue(errs, "expected structured errors")
            self.assertEqual(errs[0].get("kind"), "missing_file")
            self.assertEqual(errs[0].get("path"), "missing/file.txt")

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


class TestVerifyDeepHardening(_SkipMountValidationMixin, unittest.TestCase):
    def test_create_file_backup_fails_when_manifest_missing_in_archive_after_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            src = base / "src"
            src.mkdir()
            (src / "a.txt").write_text("x", encoding="utf-8")
            arch = base / "b.tar.gz"
            with patch("modules.backup_engine.archive_contains_manifest", return_value=False):
                res = create_file_backup(
                    [src / "a.txt"],
                    archive_path=arch,
                    allowed_source_prefixes=(base,),
                    allowed_output_prefixes=(base,),
                )
            self.assertFalse(res.ok, res.detail)
            self.assertEqual(res.message_key, K_BACKUP_FAILED_MANIFEST_MISSING)
            self.assertFalse(arch.exists(), "partial archive must be removed")

    def test_verify_deep_rejects_corrupt_manifest_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            arch = base / "bad-man.tar.gz"
            with tarfile.open(arch, "w:gz") as tf:
                raw = b"{ not json"
                info = tarfile.TarInfo(name="MANIFEST.json")
                info.size = len(raw)
                tf.addfile(info, io.BytesIO(raw))
            ok, key, det = verify_deep(arch, extract_root=base, try_loop_mount_image=False)
            self.assertFalse(ok)
            self.assertEqual(key, "backup_recovery.error.missing_manifest")
            kinds = {e.get("kind") for e in (det.get("errors") or [])}
            self.assertIn("invalid_manifest_json", kinds)

    def test_verify_deep_hardlink_matches_target_sha256(self):
        import hashlib

        data = b"shared-payload-bytes"
        h = hashlib.sha256(data).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            arch = base / "hl.tar.gz"
            man = {
                "version": 1,
                "kind": "setuphelfer-backup-manifest",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "entries": [
                    {"path": "tgt.bin", "type": "file", "size": str(len(data)), "sha256": h},
                    {"path": "hl.bin", "type": "hardlink", "link_target": "tgt.bin"},
                ],
                "skipped": [],
                "skipped_inputs": [],
                "skipped_members": [],
                "partition_layout_sfdisk_d": "",
                "system": {},
            }
            raw_man = json.dumps(man).encode("utf-8")
            with tarfile.open(arch, "w:gz") as tf:
                mi = tarfile.TarInfo(name="MANIFEST.json")
                mi.size = len(raw_man)
                tf.addfile(mi, io.BytesIO(raw_man))
                ti = tarfile.TarInfo(name="tgt.bin")
                ti.size = len(data)
                tf.addfile(ti, io.BytesIO(data))
                hi = tarfile.TarInfo(name="hl.bin")
                hi.type = tarfile.LNKTYPE
                hi.linkname = "tgt.bin"
                hi.size = 0
                tf.addfile(hi)
            ok, key, det = verify_deep(arch, extract_root=base, try_loop_mount_image=False)
            self.assertTrue(ok, (key, det))
            self.assertTrue(det.get("valid"))

    def test_verify_deep_hardlink_fails_when_target_sha256_wrong_in_manifest(self):
        import hashlib

        data = b"shared-payload-bytes"
        h_bad = hashlib.sha256(b"other").hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            arch = base / "hl-bad.tar.gz"
            man = {
                "version": 1,
                "kind": "setuphelfer-backup-manifest",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "entries": [
                    {"path": "tgt.bin", "type": "file", "size": str(len(data)), "sha256": h_bad},
                    {"path": "hl.bin", "type": "hardlink", "link_target": "tgt.bin"},
                ],
                "skipped": [],
                "skipped_inputs": [],
                "skipped_members": [],
                "partition_layout_sfdisk_d": "",
                "system": {},
            }
            raw_man = json.dumps(man).encode("utf-8")
            with tarfile.open(arch, "w:gz") as tf:
                mi = tarfile.TarInfo(name="MANIFEST.json")
                mi.size = len(raw_man)
                tf.addfile(mi, io.BytesIO(raw_man))
                ti = tarfile.TarInfo(name="tgt.bin")
                ti.size = len(data)
                tf.addfile(ti, io.BytesIO(data))
                hi = tarfile.TarInfo(name="hl.bin")
                hi.type = tarfile.LNKTYPE
                hi.linkname = "tgt.bin"
                hi.size = 0
                tf.addfile(hi)
            ok, key, det = verify_deep(arch, extract_root=base, try_loop_mount_image=False)
            self.assertFalse(ok)
            self.assertEqual(key, K_VERIFY_INTEGRITY_FAILED)
            kinds = [e.get("kind") for e in (det.get("errors") or [])]
            self.assertIn("hash_mismatch", kinds)

    def test_verify_deep_rejects_truncated_gzip(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            src = base / "src"
            src.mkdir()
            (src / "a.txt").write_text("hello", encoding="utf-8")
            arch = base / "good.tar.gz"
            res = create_file_backup(
                [src / "a.txt"],
                archive_path=arch,
                allowed_source_prefixes=(base,),
                allowed_output_prefixes=(base,),
            )
            self.assertTrue(res.ok, res.detail)
            full = arch.read_bytes()
            raw = full[: max(len(full) // 2, 10)]
            bad = base / "trunc.tar.gz"
            bad.write_bytes(raw)
            ok, key, det = verify_deep(bad, extract_root=base, try_loop_mount_image=False)
            self.assertFalse(ok)
            self.assertEqual(key, K_ARCHIVE_CORRUPT)
            self.assertEqual((det.get("errors") or [{}])[0].get("kind"), "gzip_corrupt")


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
            ent0 = (m.get("entries") or m.get("files") or [{}])[0]
            self.assertEqual(ent0.get("sha256"), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")


class TestEmbedManifestInTar(unittest.TestCase):
    def test_embed_adds_manifest_to_plain_tar_gz(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            raw = base / "plain.tar.gz"
            hello = base / "hello.txt"
            hello.write_text("hello", encoding="utf-8")
            with tarfile.open(raw, "w:gz") as tf:
                tf.add(hello, arcname="hello.txt")
            ok, err = embed_manifest_in_tar_gz(raw)
            self.assertTrue(ok, err)
            with tarfile.open(raw, "r:gz") as tf:
                first = tf.getmembers()[0].name.lstrip("./")
                self.assertEqual(first, "MANIFEST.json")
                data = tf.extractfile("MANIFEST.json")
                assert data is not None
                man = json.loads(data.read().decode("utf-8"))
                self.assertEqual(man.get("kind"), "setuphelfer-backup-manifest")
                self.assertIn("entries", man)
                paths = {e.get("path") for e in (man.get("entries") or [])}
                self.assertIn("hello.txt", paths)


class TestDdSmoke(unittest.TestCase):
    def test_create_image_backup_mocked(self):
        from subprocess import CompletedProcess

        from modules.backup_engine import create_image_backup
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.img"

            def fake_run(argv, **kwargs):
                if argv[:2] == ["lsblk", "-J"]:
                    return CompletedProcess(argv, 0, json.dumps(_lsblk_usb_sda_whole()), "")
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


class TestBackupTargetMountValidation(unittest.TestCase):
    def test_classify_devices_categories(self) -> None:
        devices = [
            {
                "device": "/dev/sda1",
                "partitions": [],
                "fstype": "ext4",
                "mountpoint": "/",
                "size": "100G",
                "type": "part",
            },
            {
                "device": "/dev/sda2",
                "partitions": [],
                "fstype": "ext4",
                "mountpoint": "/mnt/bak",
                "size": "50G",
                "type": "part",
            },
            {
                "device": "/dev/loop0",
                "partitions": [],
                "fstype": "squashfs",
                "mountpoint": "/rofs",
                "size": "2G",
                "type": "loop",
            },
            {
                "device": "/dev/sda3",
                "partitions": [],
                "fstype": "vfat",
                "mountpoint": "/boot/efi",
                "size": "512M",
                "type": "part",
            },
        ]
        c = classify_devices(devices)
        self.assertEqual(c[0]["category"], "system_disk")
        self.assertEqual(c[1]["category"], "backup_candidate")
        self.assertEqual(c[2]["category"], "live_system")
        self.assertEqual(c[3]["category"], "unknown")

    def test_validate_rejects_root_filesystem(self) -> None:
        def fake_run(argv, **kwargs):
            if argv[:2] == ["findmnt", "-J"]:
                body = {
                    "filesystems": [
                        {"source": "/dev/sda1", "target": "/", "fstype": "ext4"},
                    ]
                }
                return CompletedProcess(argv, 0, json.dumps(body), "")
            return CompletedProcess(argv, 0, "", "")

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            arch = base / "b.tar.gz"
            arch.parent.mkdir(parents=True, exist_ok=True)
            with self.assertRaises(BackupTargetValidationError) as ctx:
                validate_backup_target(arch, runner=fake_run)
            self.assertEqual(ctx.exception.message_key, "backup_recovery.error.backup_target_root_filesystem")

    def test_validate_rejects_not_mounted(self) -> None:
        def fake_run(argv, **kwargs):
            if argv[:2] == ["findmnt", "-J"]:
                return CompletedProcess(argv, 1, "", "not found")
            return CompletedProcess(argv, 0, "", "")

        with tempfile.TemporaryDirectory() as tmp:
            arch = Path(tmp) / "b.tar.gz"
            with self.assertRaises(BackupTargetValidationError) as ctx:
                validate_backup_target(arch, runner=fake_run)
            self.assertEqual(ctx.exception.message_key, "backup_recovery.error.backup_target_not_mounted")

    def test_validate_accepts_ext4_block_device_mount(self) -> None:
        def inner(argv, **kwargs):
            if argv[:2] == ["findmnt", "-J"]:
                mount_at = str(Path(argv[2]).resolve())
                body = {
                    "filesystems": [
                        {"source": "/dev/sdb1", "target": mount_at, "fstype": "ext4"},
                    ]
                }
                return CompletedProcess(argv, 0, json.dumps(body), "")
            return CompletedProcess(argv, 0, "", "")

        _T_SAFE.mkdir(parents=True, exist_ok=True)
        base = _T_SAFE / "ext4ok"
        base.mkdir(parents=True, exist_ok=True)
        fake_run = _wrap_fake_run_with_lsblk(inner, str(base.resolve()))
        arch = base / "b.tar.gz"
        validate_backup_target(arch, runner=fake_run)

    def test_validate_rejects_unwritable_directory(self) -> None:
        def inner(argv, **kwargs):
            if argv[:2] == ["findmnt", "-J"]:
                mount_at = str(Path(argv[2]).resolve())
                body = {
                    "filesystems": [
                        {"source": "/dev/sdb1", "target": mount_at, "fstype": "ext4"},
                    ]
                }
                return CompletedProcess(argv, 0, json.dumps(body), "")
            return CompletedProcess(argv, 0, "", "")

        _T_SAFE.mkdir(parents=True, exist_ok=True)
        base = _T_SAFE / "unwritable"
        base.mkdir(parents=True, exist_ok=True)
        d = base / "mount_here"
        d.mkdir()
        fake_run = _wrap_fake_run_with_lsblk(inner, str(d.resolve()))
        try:
            os.chmod(d, 0o555)
            arch = d / "b.tar.gz"
            with self.assertRaises(BackupTargetValidationError) as ctx:
                validate_backup_target(arch, runner=fake_run)
            self.assertEqual(ctx.exception.message_key, K_BACKUP_TARGET_NOT_WRITABLE)
        finally:
            os.chmod(d, 0o700)

    def test_assert_writable_ok_on_tmp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            assert_backup_target_dir_writable(Path(tmp))

    def test_writable_probe_detail_mentions_group_when_gid_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "w"
            d.mkdir()
            # Kein patch auf os.stat (Path.is_dir nutzt os.stat global).
            with patch("modules.storage_detection.os.open", side_effect=PermissionError("denied")):
                with patch(
                    "modules.storage_detection.grp.getgrnam",
                    return_value=type("G", (), {"gr_gid": 12345678})(),
                ):
                    with self.assertRaises(BackupTargetValidationError) as ctx:
                        assert_backup_target_dir_writable(d)
            self.assertIn("Gruppe", ctx.exception.detail or "")

    def test_validate_rejects_squashfs(self) -> None:
        def fake_run(argv, **kwargs):
            if argv[:2] == ["findmnt", "-J"]:
                mount_at = str(Path(argv[2]).resolve())
                body = {
                    "filesystems": [
                        {"source": "/dev/loop0", "target": mount_at, "fstype": "squashfs"},
                    ]
                }
                return CompletedProcess(argv, 0, json.dumps(body), "")
            return CompletedProcess(argv, 0, "", "")

        with tempfile.TemporaryDirectory() as tmp:
            arch = Path(tmp) / "b.tar.gz"
            with self.assertRaises(BackupTargetValidationError) as ctx:
                validate_backup_target(arch, runner=fake_run)
            self.assertEqual(ctx.exception.message_key, "backup_recovery.error.backup_target_live_filesystem")

    def test_validate_rejects_tmpfs_non_block_source(self) -> None:
        def fake_run(argv, **kwargs):
            if argv[:2] == ["findmnt", "-J"]:
                mount_at = str(Path(argv[2]).resolve())
                body = {
                    "filesystems": [
                        {"source": "tmpfs", "target": mount_at, "fstype": "tmpfs"},
                    ]
                }
                return CompletedProcess(argv, 0, json.dumps(body), "")
            return CompletedProcess(argv, 0, "", "")

        with tempfile.TemporaryDirectory() as tmp:
            arch = Path(tmp) / "b.tar.gz"
            with self.assertRaises(BackupTargetValidationError) as ctx:
                validate_backup_target(arch, runner=fake_run)
            self.assertEqual(ctx.exception.message_key, "backup_recovery.error.backup_target_non_block_source")

    def test_create_file_backup_aborts_on_validation_failure(self) -> None:
        def fake_run(argv, **kwargs):
            if argv[:2] == ["findmnt", "-J"]:
                return CompletedProcess(argv, 1, "", "no")
            return CompletedProcess(argv, 0, "", "")

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            src = base / "src"
            src.mkdir()
            (src / "a.txt").write_text("x", encoding="utf-8")
            arch = base / "b.tar.gz"
            res = create_file_backup(
                [src / "a.txt"],
                archive_path=arch,
                allowed_source_prefixes=(base,),
                allowed_output_prefixes=(base,),
                runner=fake_run,
            )
            self.assertFalse(res.ok)
            self.assertEqual(res.message_key, "backup_recovery.error.backup_target_not_mounted")


if __name__ == "__main__":
    unittest.main()
