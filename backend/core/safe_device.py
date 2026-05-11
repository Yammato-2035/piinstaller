"""
Sichere Schreibziele: Geräteerkennung, Klassifikation, Allowlist, validate_write_target.

DETECT ≠ WRITE: alle Blockgeräte können erkannt werden; Schreibzugriffe nur nach harter Prüfung.
"""

from __future__ import annotations

import json
import os
import re
import stat
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from core.block_device_allowlist import is_allowed_block_device, normalize_block_device
from core.rescue_allowlist import RESCUE_DRYRUN_WRITE_PREFIXES, path_under_prefixes

Runner = Callable[..., Any]

# Erlaubte Präfixe für Schreibpfade (Backup, Rescue-Staging, USB-Mount des Produkts).
_DEFAULT_WRITE_PREFIX_STR: tuple[str, ...] = (
    "/mnt/setuphelfer",
    "/mnt/pi-installer-usb",
    "/mnt/pi-installer-clone",
    "/mnt/setuphelfer-restore-live",
    "/tmp/setuphelfer-test",
    "/tmp/setuphelfer-rescue-dryrun-staging",
    "/tmp/setuphelfer-restore-test",
    "/tmp/setuphelfer-rescue-restore-test",
    "/tmp/setuphelfer-rescue-dryrun-state",
)

# Explizit unsichere Mount-Bäume für Schreibziele (Fail-Fast).
_DIAG_SYSTEM = "STORAGE-PROTECTION-001"
_DIAG_BOOT = "STORAGE-PROTECTION-002"
_DIAG_FOREIGN = "STORAGE-PROTECTION-003"
_DIAG_NOT_ALLOWLIST = "STORAGE-PROTECTION-004"
_DIAG_UNSAFE_MOUNT = "STORAGE-PROTECTION-005"

_NTFS_LARGE_BYTES = 50 * 1024 * 1024 * 1024


class WriteTargetProtectionError(ValueError):
    """Schreibziel verboten; diagnosis_id für API/Diagnose-Matcher."""

    def __init__(self, diagnosis_id: str, message: str, *, detail: str | None = None) -> None:
        self.diagnosis_id = diagnosis_id
        self.detail = detail
        super().__init__(message)


def _run(argv: list[str], *, runner: Runner | None = None, timeout: int = 60) -> Any:
    run = runner or __import__("subprocess").run
    return run(argv, capture_output=True, text=True, timeout=timeout, check=False)


def write_safe_prefixes_resolved() -> tuple[Path, ...]:
    env = (os.environ.get("SETUPHELFER_BACKUP_WRITE_PREFIXES") or "").strip()
    if env:
        out: list[Path] = []
        for part in env.split(","):
            p = part.strip()
            if not p:
                continue
            out.append(Path(p).resolve())
        return tuple(out)
    return tuple(Path(p).resolve() for p in _DEFAULT_WRITE_PREFIX_STR)


def _path_under_any_prefix(p: Path, prefixes: Sequence[Path]) -> bool:
    rp = _resolved(p)
    for root in prefixes:
        br = _resolved(root)
        try:
            rp.relative_to(br)
            return True
        except ValueError:
            if rp == br:
                return True
    return False


def _resolved(p: Path) -> Path:
    try:
        return p.resolve()
    except OSError:
        return p


def _assert_abs_path_safe_chars(path_str: str) -> None:
    if not isinstance(path_str, str):
        raise WriteTargetProtectionError(_DIAG_NOT_ALLOWLIST, "Pfad muss ein String sein")
    stripped = path_str.strip()
    if not stripped.startswith("/"):
        raise WriteTargetProtectionError(_DIAG_NOT_ALLOWLIST, "Pfad muss absolut sein")
    forbidden = ["\n", "\r", "\t", "\x00", "`", "$", ";", "&", "|", "<", ">", "!", "\"", "'"]
    if any(ch in stripped for ch in forbidden):
        raise WriteTargetProtectionError(_DIAG_NOT_ALLOWLIST, "Pfad enthält verbotene Zeichen")


def _parse_size_bytes(s: Any) -> int:
    if not isinstance(s, str):
        return 0
    t = s.strip().upper().replace(" ", "")
    if not t or t == "-":
        return 0
    m = re.match(r"^([\d.]+)([KMGTPE]?)([I]?)?B?$", t)
    if not m:
        return 0
    num = float(m.group(1))
    u = m.group(2) or ""
    binary = m.group(3) == "I" or (m.group(3) == "" and u in {"K", "M", "G", "T", "P", "E"})
    mult = 1024 if binary else 1000
    pow_map = {"": 0, "K": 1, "M": 2, "G": 3, "T": 4, "P": 5, "E": 6}
    exp = pow_map.get(u, 0)
    return int(num * (mult**exp))


def _lsblk_tree(*, runner: Runner | None = None) -> dict[str, Any]:
    cols = "PATH,NAME,TYPE,SIZE,FSTYPE,MOUNTPOINTS,RM,RO,MODEL,TRAN,PKNAME,PARTLABEL"
    r = _run(["lsblk", "-J", "-o", cols], runner=runner, timeout=30)
    if r.returncode != 0 or not (r.stdout or "").strip():
        r = _run(
            ["lsblk", "-J", "-o", "NAME,TYPE,SIZE,FSTYPE,MOUNTPOINTS,RM,RO,MODEL,TRAN,PKNAME,PARTLABEL"],
            runner=runner,
            timeout=30,
        )
    try:
        return json.loads(r.stdout or "{}")
    except json.JSONDecodeError:
        return {}


def _collect_mountpoints(node: Mapping[str, Any]) -> list[str]:
    out: list[str] = []
    mp = node.get("mountpoint")
    if isinstance(mp, str) and mp.strip():
        out.append(mp.strip())
    mps = node.get("mountpoints")
    if isinstance(mps, list):
        for x in mps:
            if isinstance(x, str) and x.strip():
                out.append(x.strip())
    for ch in node.get("children") or []:
        if isinstance(ch, dict):
            out.extend(_collect_mountpoints(ch))
    return sorted(set(out))


def _device_path_for_node(node: Mapping[str, Any]) -> str:
    p = node.get("path")
    if isinstance(p, str) and p.startswith("/dev/"):
        return p
    name = node.get("name")
    if isinstance(name, str) and name:
        return f"/dev/{name}" if not name.startswith("/dev/") else name
    return ""


def _infer_bus_type(name: str, tran: str) -> str:
    t = (tran or "").lower()
    if t == "usb":
        return "usb"
    if name.startswith("nvme"):
        return "nvme"
    if name.startswith("mmcblk") or name.startswith("mmc"):
        return "sd"
    if name.startswith("loop"):
        return "loop"
    if t == "nvme":
        return "nvme"
    return "ssd" if name.startswith("sd") else "disk"


def _partition_flags(node: Mapping[str, Any]) -> list[str]:
    flags: list[str] = []
    pl = node.get("partlabel")
    if isinstance(pl, str) and pl.upper() == "EFI SYSTEM PARTITION":
        flags.append("esp")
    fst = (node.get("fstype") or "")
    if isinstance(fst, str) and fst.lower() == "vfat":
        mps = _collect_mountpoints(node)
        if any("/efi" in m.lower() or m.rstrip("/").endswith("/efi") for m in mps):
            flags.append("esp")
    if "esp" not in flags:
        mps = _collect_mountpoints(node)
        if any(m in ("/boot", "/boot/firmware") or m.startswith("/boot/") for m in mps):
            flags.append("boot")
    return flags


@dataclass
class PartitionInfo:
    name: str
    device_id: str
    filesystem: str | None
    mountpoints: list[str]
    size: str | None
    size_bytes: int
    flags: list[str] = field(default_factory=list)


@dataclass
class ClassifiedDevice:
    id: str
    name: str
    type: str
    size: str | None
    removable: bool
    mountpoints: list[str]
    filesystems: list[str]
    partitions: list[PartitionInfo]
    is_system_disk: bool
    is_boot_disk: bool
    is_foreign_os_disk: bool
    is_write_allowed: bool

    def to_public_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["partitions"] = [asdict(p) for p in self.partitions]
        return d


def _windows_efi_hint(mountpoints: Sequence[str]) -> bool:
    for mp in mountpoints:
        try:
            if (Path(mp) / "EFI/Microsoft/Boot").is_dir():
                return True
        except OSError:
            continue
    return False


def _disk_foreign_heuristic(partitions: Sequence[PartitionInfo], mountpoints: Sequence[str]) -> bool:
    if _windows_efi_hint(mountpoints):
        return True
    ntfs_large = False
    has_vfat = False
    for p in partitions:
        fs = (p.filesystem or "").lower()
        if fs == "vfat":
            has_vfat = True
        if fs == "ntfs" and p.size_bytes >= _NTFS_LARGE_BYTES:
            ntfs_large = True
    return bool(ntfs_large and has_vfat)


def _classify_one_disk(
    disk_node: Mapping[str, Any],
    *,
    children: Sequence[Mapping[str, Any]],
) -> ClassifiedDevice:
    dev_id = _device_path_for_node(disk_node)
    name = disk_node.get("name")
    name_s = name if isinstance(name, str) else ""
    tran = disk_node.get("tran")
    tran_s = tran if isinstance(tran, str) else ""
    rm = disk_node.get("rm")
    removable = rm is True or rm == 1 or (isinstance(rm, str) and rm.strip() == "1")
    if tran_s.lower() == "usb":
        removable = True

    mps = _collect_mountpoints(disk_node)
    fstypes: list[str] = []
    parts_out: list[PartitionInfo] = []

    for ch in children:
        if not isinstance(ch, dict):
            continue
        t = ch.get("type")
        if t not in ("part", "crypt", "lvm", "rom"):
            continue
        ch_dev = _device_path_for_node(ch)
        fst = ch.get("fstype")
        fst_s = fst if isinstance(fst, str) else None
        if fst_s:
            fstypes.append(fst_s)
        sz = ch.get("size")
        sz_s = sz if isinstance(sz, str) else None
        pmps = _collect_mountpoints(ch)
        flags = _partition_flags(ch)
        parts_out.append(
            PartitionInfo(
                name=ch.get("name") or "",
                device_id=ch_dev,
                filesystem=fst_s,
                mountpoints=pmps,
                size=sz_s,
                size_bytes=_parse_size_bytes(sz_s),
                flags=flags,
            )
        )

    is_system = any(mp == "/" for mp in mps)
    boot_mps = ("/boot", "/boot/firmware")
    is_boot = any(mp in boot_mps or mp.startswith("/boot/") for mp in mps)
    for p in parts_out:
        for mp in p.mountpoints:
            if mp in boot_mps or mp.startswith("/boot/"):
                is_boot = True

    is_foreign = False
    if not is_system:
        is_foreign = _disk_foreign_heuristic(parts_out, mps)

    bus_type = _infer_bus_type(name_s, tran_s)

    write_ok = False
    if not is_system and not is_boot and not is_foreign:
        for mp in mps:
            try:
                rp = Path(mp).resolve()
            except OSError:
                continue
            if _path_under_any_prefix(rp, write_safe_prefixes_resolved()):
                write_ok = True
                break
        for p in parts_out:
            for mp in p.mountpoints:
                try:
                    rp = Path(mp).resolve()
                except OSError:
                    continue
                if _path_under_any_prefix(rp, write_safe_prefixes_resolved()):
                    write_ok = True
                    break

    return ClassifiedDevice(
        id=dev_id or f"/dev/{name_s}",
        name=name_s,
        type=bus_type,
        size=disk_node.get("size") if isinstance(disk_node.get("size"), str) else None,
        removable=bool(removable),
        mountpoints=sorted(set(mps)),
        filesystems=sorted(set(fstypes)),
        partitions=parts_out,
        is_system_disk=is_system,
        is_boot_disk=is_boot,
        is_foreign_os_disk=is_foreign,
        is_write_allowed=write_ok,
    )


def list_classified_devices(*, runner: Runner | None = None) -> list[ClassifiedDevice]:
    data = _lsblk_tree(runner=runner)
    raw = data.get("blockdevices")
    if not isinstance(raw, list):
        return []
    out: list[ClassifiedDevice] = []
    for node in raw:
        if not isinstance(node, dict):
            continue
        if node.get("type") != "disk":
            continue
        children = [c for c in (node.get("children") or []) if isinstance(c, dict)]
        out.append(_classify_one_disk(node, children=children))
    return out


def devices_for_api(*, runner: Runner | None = None) -> list[dict[str, Any]]:
    return [d.to_public_dict() for d in list_classified_devices(runner=runner)]


def _find_disk_node_for_block_path(block_path: str, tree: Mapping[str, Any]) -> dict[str, Any] | None:
    """Liefert den lsblk-Disk-Knoten (type=disk), zu dem block_path gehört."""
    target = normalize_block_device(block_path)
    devices = tree.get("blockdevices")
    if not isinstance(devices, list):
        return None

    def walk(nodes: list[Any], parent_disk: dict[str, Any] | None) -> dict[str, Any] | None:
        for n in nodes:
            if not isinstance(n, dict):
                continue
            dpath = _device_path_for_node(n)
            this_disk = n if n.get("type") == "disk" else parent_disk
            if dpath and dpath == target:
                if this_disk is not None and this_disk.get("type") == "disk":
                    return this_disk
                if n.get("type") == "disk":
                    return n
                return None
            ch = n.get("children") or []
            hit = walk(ch, this_disk if n.get("type") == "disk" else parent_disk)
            if hit is not None:
                return hit
        return None

    return walk(devices, None)


def _classified_for_block(block_path: str, *, runner: Runner | None = None) -> ClassifiedDevice:
    tree = _lsblk_tree(runner=runner)
    disk_node = _find_disk_node_for_block_path(block_path, tree)
    if disk_node is None:
        raise WriteTargetProtectionError(
            _DIAG_NOT_ALLOWLIST,
            "Blockgerät nicht in lsblk-Zuordnung gefunden",
            detail=block_path,
        )
    children = [c for c in (disk_node.get("children") or []) if isinstance(c, dict)]
    return _classify_one_disk(disk_node, children=children)


def _find_existing_anchor(path: Path) -> Path:
    cur = path
    for _ in range(512):
        try:
            if cur.exists():
                return cur
        except OSError:
            pass
        if cur == cur.parent:
            break
        cur = cur.parent
    return Path("/")


def _findmnt_for_path(anchor: Path, *, runner: Runner | None = None) -> dict[str, Any] | None:
    r = _run(["findmnt", "-J", str(anchor)], runner=runner, timeout=30)
    if r.returncode != 0:
        return None
    try:
        data = json.loads(r.stdout or "{}")
    except json.JSONDecodeError:
        return None
    fss = data.get("filesystems")
    if not isinstance(fss, list) or not fss:
        return None
    try:
        sp = str(anchor.resolve())
    except OSError:
        sp = str(anchor.absolute())
    best: dict[str, Any] | None = None
    best_len = -1
    for fs in fss:
        if not isinstance(fs, dict):
            continue
        tgt = fs.get("target")
        if not isinstance(tgt, str) or not tgt:
            continue
        tnorm = tgt.rstrip("/") or "/"
        if sp == tnorm or sp.startswith(tnorm + "/"):
            ln = len(tnorm)
            if ln > best_len:
                best_len = ln
                best = fs
    return best or (fss[-1] if isinstance(fss[-1], dict) else None)


def _simple_block_source(src: str) -> bool:
    s = src.strip()
    if not s.startswith("/dev/"):
        return False
    if "mapper" in s:
        return False
    # Whole disk + Partitionen (kein mapper)
    return bool(
        re.match(r"^/dev/sd[a-z]+(?:\d+)?$", s)
        or re.match(r"^/dev/nvme\d+n\d+(?:p\d+)?$", s)
        or re.match(r"^/dev/mmcblk\d+(?:p\d+)?$", s)
    )


def _is_block_device_path(dev_path: str) -> bool:
    try:
        st = os.stat(dev_path)
    except OSError:
        return False
    return stat.S_ISBLK(st.st_mode)


def _is_known_block_source_via_lsblk(dev_path: str, *, runner: Runner | None = None) -> bool:
    tree = _lsblk_tree(runner=runner)
    disk_node = _find_disk_node_for_block_path(dev_path, tree)
    return disk_node is not None


def _resolve_block_source_candidate(src: str, *, runner: Runner | None = None) -> tuple[str | None, str]:
    """
    Liefert (resolved_source, reason).
    Erlaubt nur konservative echte Blockpfade:
    - /dev/sdX[/N], /dev/nvmeXnY[pN], /dev/mmcblkN[pN]
    - /dev/disk/by-uuid/* -> realpath auf obige Formen
    """
    s = (src or "").strip()
    if not s:
        return None, "empty_source"
    if "mapper" in s:
        return None, "mapper_not_allowed"
    if s.startswith("/dev/disk/by-uuid/"):
        try:
            rp = os.path.realpath(s)
        except OSError:
            return None, "uuid_realpath_failed"
        if not rp.startswith("/dev/"):
            return None, "uuid_realpath_not_dev"
        if "mapper" in rp:
            return None, "uuid_mapper_not_allowed"
        if not _simple_block_source(rp):
            return None, "uuid_realpath_not_simple_block"
        if not _is_block_device_path(rp):
            if _is_known_block_source_via_lsblk(rp, runner=runner):
                return rp, "uuid_resolved_known_via_lsblk"
            return None, "uuid_realpath_not_block_device"
        return rp, "uuid_resolved"
    if not _simple_block_source(s):
        return None, "not_simple_block_source"
    if not _is_block_device_path(s):
        if _is_known_block_source_via_lsblk(s, runner=runner):
            return s, "simple_block_known_via_lsblk"
        return None, "not_block_device"
    return s, "simple_block_source"


def _flatten_findmnt_nodes(nodes: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(nodes, list):
        return out
    for n in nodes:
        if not isinstance(n, dict):
            continue
        out.append(n)
        ch = n.get("children")
        if isinstance(ch, list):
            out.extend(_flatten_findmnt_nodes(ch))
    return out


def _findmnt_entries_for_path(path: Path, *, runner: Runner | None = None) -> list[dict[str, Any]]:
    r = _run(["findmnt", "-J", "-T", str(path)], runner=runner, timeout=30)
    if r.returncode != 0:
        return []
    try:
        data = json.loads(r.stdout or "{}")
    except json.JSONDecodeError:
        return []
    fss = data.get("filesystems")
    return _flatten_findmnt_nodes(fss)


def _findmnt_entries_recursive(target: str, *, runner: Runner | None = None) -> list[dict[str, Any]]:
    r = _run(["findmnt", "-J", "-R", target], runner=runner, timeout=30)
    if r.returncode != 0:
        return []
    try:
        data = json.loads(r.stdout or "{}")
    except json.JSONDecodeError:
        return []
    fss = data.get("filesystems")
    return _flatten_findmnt_nodes(fss)


def resolve_mount_source_for_path(path: str | Path, *, runner: Runner | None = None) -> dict[str, str]:
    """
    Robuste Mount-Source-Auflösung für systemd-automount/autofs.
    Bei Unsicherheit bleibt die Entscheidung konservativ (kein resolved_source).
    """
    p = path if isinstance(path, Path) else Path(str(path))
    try:
        anchor = _find_existing_anchor(p.resolve())
    except OSError:
        anchor = _find_existing_anchor(p)

    entries = _findmnt_entries_for_path(anchor, runner=runner)
    if not entries:
        return {
            "mount_source_seen": "",
            "resolved_source": "",
            "fstype": "",
            "target": str(anchor),
            "reason": "findmnt_t_no_entries",
        }

    # Für Diagnosezwecke: was wurde zuerst gesehen?
    first = entries[0]
    first_src = str(first.get("source") or "")
    first_fst = str(first.get("fstype") or "")
    first_tgt = str(first.get("target") or str(anchor))

    def _pick(entries_in: list[dict[str, Any]]) -> tuple[str, str, str, str] | None:
        best: tuple[int, str, str, str, str] | None = None
        for fs in entries_in:
            src = str(fs.get("source") or "").strip()
            fst = str(fs.get("fstype") or "").strip()
            tgt = str(fs.get("target") or "").strip()
            resolved, why = _resolve_block_source_candidate(src, runner=runner)
            if not resolved:
                continue
            score = 0
            if fst.lower() != "autofs":
                score += 40
            if src.startswith("/dev/"):
                score += 20
            if tgt:
                score += len(tgt)
            if best is None or score > best[0]:
                best = (score, src, resolved, fst, tgt)
        if best is None:
            return None
        return best[1], best[2], best[3], best[4]

    chosen = _pick(entries)
    if chosen is None:
        # Bei systemd-automount ggf. zuerst Triggern (stat/listdir) und einmal -T neu lesen.
        looks_automount_now = any(
            str(fs.get("fstype") or "").lower() == "autofs"
            or str(fs.get("source") or "").startswith("systemd-")
            for fs in entries
        )
        if looks_automount_now:
            try:
                os.stat(str(anchor))
            except OSError:
                pass
            try:
                if anchor.is_dir():
                    next(anchor.iterdir(), None)
            except (OSError, StopIteration):
                pass
            retry_entries = _findmnt_entries_for_path(anchor, runner=runner)
            chosen = _pick(retry_entries)
            if chosen is not None:
                seen_src, resolved_src, fstype, target = chosen
                return {
                    "mount_source_seen": seen_src or first_src,
                    "resolved_source": resolved_src,
                    "fstype": fstype or first_fst,
                    "target": target or first_tgt,
                    "reason": "ok_after_automount_trigger",
                }

        # automount/autofs-Layer gesehen? Dann rekursiv denselben TARGET-Baum prüfen.
        looks_automount = any(
            str(fs.get("fstype") or "").lower() == "autofs"
            or str(fs.get("source") or "").startswith("systemd-")
            for fs in entries
        )
        if looks_automount:
            rec = _findmnt_entries_recursive(first_tgt or str(anchor), runner=runner)
            chosen = _pick(rec)
            if chosen is None:
                return {
                    "mount_source_seen": first_src,
                    "resolved_source": "",
                    "fstype": first_fst,
                    "target": first_tgt,
                    "reason": "automount_layer_no_resolved_block_source",
                }
        else:
            return {
                "mount_source_seen": first_src,
                "resolved_source": "",
                "fstype": first_fst,
                "target": first_tgt,
                "reason": "no_resolvable_block_source",
            }

    seen_src, resolved_src, fstype, target = chosen
    return {
        "mount_source_seen": seen_src or first_src,
        "resolved_source": resolved_src,
        "fstype": fstype or first_fst,
        "target": target or first_tgt,
        "reason": "ok",
    }


def _fail_from_classification(cd: ClassifiedDevice) -> None:
    if cd.is_system_disk:
        raise WriteTargetProtectionError(
            _DIAG_SYSTEM,
            "Schreibzugriff auf Systemplatte ist nicht erlaubt",
            detail=cd.id,
        )
    if cd.is_boot_disk:
        raise WriteTargetProtectionError(
            _DIAG_BOOT,
            "Schreibzugriff auf Boot-Medium ist nicht erlaubt",
            detail=cd.id,
        )
    if cd.is_foreign_os_disk:
        raise WriteTargetProtectionError(
            _DIAG_FOREIGN,
            "Fremdes Betriebssystem (z. B. Windows) erkannt — Schreibzugriff verboten",
            detail=cd.id,
        )


def validate_write_target(target: str | Path, *, runner: Runner | None = None) -> None:
    """
    Harte Prüfung vor jedem Schreibzugriff auf einen Blockpfad oder ein Backup-Verzeichnis.

    - Verzeichnis: muss unter write_safe_prefixes liegen; Ausnahme: echte externe Mounts
      unter /media oder /run/media werden nach Mount-/Device-Prüfung gezielt erlaubt.
      Geschützte System-/Boot-/Windows-Platten bleiben gesperrt.
    - Blockgerät (/dev/...): Muster-Allowlist + gleiche Klassifikation auf der zugehörigen Disk.
    """
    raw = str(target).strip()
    if raw.startswith("/dev/"):
        _validate_block_write(raw, runner=runner)
    else:
        _validate_dir_write(Path(raw), runner=runner)


def _canonical_whole_disk(dev_path: str) -> str:
    """Mappt Partitionen (nvme0n1p1, sda1, mmcblk0p2) auf das Whole-Disk-Gerät."""
    d = normalize_block_device(dev_path)
    if re.match(r"^/dev/nvme\d+n\d+p\d+$", d):
        return re.sub(r"p\d+$", "", d)
    if re.match(r"^/dev/mmcblk\d+p\d+$", d):
        return re.sub(r"p\d+$", "", d)
    if re.match(r"^/dev/sd[a-z]+\d+$", d):
        return re.sub(r"\d+$", "", d)
    return d


def _validate_block_write(dev_path: str, *, runner: Runner | None = None) -> None:
    whole = _canonical_whole_disk(dev_path)
    if not is_allowed_block_device(whole):
        raise WriteTargetProtectionError(
            _DIAG_NOT_ALLOWLIST,
            "Blockgerät entspricht nicht dem erlaubten Whole-Disk-Muster",
            detail=dev_path,
        )
    cd = _classified_for_block(dev_path, runner=runner)
    _fail_from_classification(cd)


def _validate_dir_write(path: Path, *, runner: Runner | None = None) -> None:
    _assert_abs_path_safe_chars(str(path))
    try:
        resolved = path.resolve()
    except OSError as e:
        raise WriteTargetProtectionError(_DIAG_NOT_ALLOWLIST, "Pfad konnte nicht aufgelöst werden", detail=str(e)) from e

    rs = str(resolved)
    is_media_tree = rs.startswith("/media/") or rs.startswith("/run/media/")

    if str(resolved) == "/":
        raise WriteTargetProtectionError(_DIAG_SYSTEM, "Root ist kein erlaubtes Schreibziel")

    allowed = write_safe_prefixes_resolved()
    if not is_media_tree and not _path_under_any_prefix(resolved, allowed):
        raise WriteTargetProtectionError(
            _DIAG_NOT_ALLOWLIST,
            "Pfad liegt nicht unter einem freigegebenen Schreibpräfix",
            detail=str(resolved),
        )

    # Rescue-Dry-Run: findmnt liefert auf tiefer Sandbox oft nichts — Präfix reicht.
    if path_under_prefixes(resolved, RESCUE_DRYRUN_WRITE_PREFIXES):
        return

    mount_info = resolve_mount_source_for_path(resolved, runner=runner)
    resolved_source = mount_info.get("resolved_source") or ""
    fstype = str(mount_info.get("fstype") or "").strip().lower()
    if not resolved_source:
        diag = _DIAG_UNSAFE_MOUNT if is_media_tree else _DIAG_NOT_ALLOWLIST
        reason = (
            "Mount-Quelle ist kein einfaches Blockgerät (z. B. mapper)"
            f" [mount_source_seen={mount_info.get('mount_source_seen') or '(empty)'}; "
            f"resolved_source={mount_info.get('resolved_source') or '(none)'}; "
            f"fstype={mount_info.get('fstype') or '(unknown)'}; "
            f"target={mount_info.get('target') or '(unknown)'}; "
            f"reason={mount_info.get('reason') or 'unknown'}]"
        )
        raise WriteTargetProtectionError(diag, reason, detail=mount_info)
    if is_media_tree:
        # /media ist nur erlaubt, wenn ein reales lokales Blockdevice gemountet ist.
        if not resolved_source.startswith("/dev/"):
            raise WriteTargetProtectionError(
                _DIAG_UNSAFE_MOUNT,
                "Schreibziel unter /media ohne lokales Blockgerät ist nicht erlaubt",
                detail=str(mount_info),
            )
        whole_src = _canonical_whole_disk(resolved_source)
        if whole_src.startswith("/dev/loop") or fstype in ("tmpfs", "overlay"):
            raise WriteTargetProtectionError(
                _DIAG_UNSAFE_MOUNT,
                "Schreibziel unter /media ist auf unsicherem Dateisystem/Device nicht erlaubt",
                detail=str(mount_info),
            )
    cd = _classified_for_block(resolved_source, runner=runner)
    _fail_from_classification(cd)


def protection_signal_map(exc: WriteTargetProtectionError) -> dict[str, str]:
    """Signale für POST /api/diagnostics/analyze (Wert wird von normalized_signals lowercased)."""
    return {"storage_protection": exc.diagnosis_id.lower()}


__all__ = [
    "ClassifiedDevice",
    "PartitionInfo",
    "WriteTargetProtectionError",
    "devices_for_api",
    "list_classified_devices",
    "protection_signal_map",
    "validate_write_target",
    "write_safe_prefixes_resolved",
]
