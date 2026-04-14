#!/usr/bin/env python3
"""
Isolierter Restore-Zwischentest: entpackt ein Backup nur nach /tmp/setuphelfer-restore-test.

- Kein Restore auf /, keine Systemänderung außerhalb von /tmp.
- Nutzt die echte Restore-Funktion restore_files() mit Allowlist.

Aufruf:
  cd <Repo-Root> && PYTHONPATH=backend python3 tools/setuphelfer_restore_isolated_test.py
  SETUPHELFER_RESTORE_TEST_ARCHIVE=/pfad/zum/backup.tar.gz python3 tools/setuphelfer_restore_isolated_test.py

Ohne Umgebungsvariable/Argument: es wird unter /tmp ein synthetischer etc/-Baum erzeugt,
mit create_file_backup archiviert (gleicher Engine-Codepfad wie Produktion), dann restored.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BACKEND = REPO / "backend"
RESTORE_ROOT = Path("/tmp/setuphelfer-restore-test")
# Allowlist exakt das Ziel (kein Umgehen der Prüfung)
ALLOW_PREFIXES = (RESTORE_ROOT,)


def _ensure_backend_path() -> None:
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))


def _prepare_target_dir() -> None:
    if RESTORE_ROOT.exists():
        shutil.rmtree(RESTORE_ROOT)
    RESTORE_ROOT.mkdir(mode=0o755, parents=True, exist_ok=True)


def _build_synthetic_etc_tree(base: Path) -> None:
    """Minimaler Baum mit Symlinks analog typischer Debian-/etc-Konstellationen."""
    im = base / "etc" / "ImageMagick-7"
    im.mkdir(parents=True, exist_ok=True)
    (im / "colors.xml").write_text("<colors/>\n", encoding="utf-8")
    alsa = base / "etc" / "alsa" / "conf.d"
    alsa.mkdir(parents=True, exist_ok=True)
    pipe_target = "/usr/share/alsa/alsa.conf.d/50-pipewire.conf"
    (alsa / "50-pipewire.conf").symlink_to(pipe_target)
    alt = base / "etc" / "alternatives"
    alt.mkdir(parents=True, exist_ok=True)
    (alt / "awk").symlink_to("/usr/bin/mawk")


def _create_synthetic_archive() -> Path:
    tmp_parent = Path(tempfile.mkdtemp(prefix="setuphelfer_synth_src_", dir="/tmp"))
    try:
        _build_synthetic_etc_tree(tmp_parent)
        arch = Path("/tmp/setuphelfer-restore-selftest-input.tar.gz")
        if arch.exists():
            arch.unlink()
        _ensure_backend_path()
        from modules.backup_engine import create_file_backup

        res = create_file_backup(
            [tmp_parent / "etc"],
            archive_path=arch,
            allowed_source_prefixes=(tmp_parent,),
            allowed_output_prefixes=(Path("/tmp"),),
        )
        if not res.ok:
            raise RuntimeError(f"create_file_backup failed: {res.detail}")
        return arch
    finally:
        shutil.rmtree(tmp_parent, ignore_errors=True)


def _all_paths_under(root: Path) -> list[Path]:
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        dp = Path(dirpath)
        for n in dirnames + filenames:
            out.append(dp / n)
    return out


def _validate_containment(root: Path) -> tuple[bool, str | None]:
    """Prüft, dass alle archivierten Knoten unter root liegen (ohne Symlink-Ziele aufzulösen)."""
    root_r = root.resolve()
    for p in _all_paths_under(root):
        try:
            node = p.absolute()
            node.relative_to(root_r)
        except ValueError:
            return False, f"path node outside restore root: {p}"
    return True, None


def main() -> int:
    _ensure_backend_path()
    from modules.restore_engine import restore_files

    archive = os.environ.get("SETUPHELFER_RESTORE_TEST_ARCHIVE", "").strip()
    if len(sys.argv) > 1:
        archive = sys.argv[1]
    archive_path = Path(archive) if archive else None

    if archive_path is None or not archive_path.is_file():
        print("Kein Archiv übergeben – erzeuge synthetisches Archiv via create_file_backup …")
        archive_path = _create_synthetic_archive()
    print(f"Archiv: {archive_path}")

    _prepare_target_dir()

    ok, key, detail = restore_files(
        archive_path,
        RESTORE_ROOT,
        allowed_target_prefixes=ALLOW_PREFIXES,
        dry_run=False,
    )
    print(f"restore_files ok={ok} key={key} detail={detail!r}")
    if not ok:
        return 1

    # --- Struktur ---
    checks: list[tuple[str, bool, str]] = []
    # Archiv kann tmp/.../etc/... flach ablegen (absolute Pfade im tar); suche etc rekursiv
    etc_dirs = [p for p in RESTORE_ROOT.rglob("etc") if p.is_dir() and p.name == "etc"]
    checks.append(("mindestens ein …/etc Verzeichnis", bool(etc_dirs), ""))

    colors = list(RESTORE_ROOT.rglob("colors.xml"))
    checks.append(
        (
            "etc/ImageMagick-7/colors.xml (irgendwo unter Restore-Wurzel)",
            any("ImageMagick-7" in str(p) for p in colors),
            str(colors[0]) if colors else "",
        )
    )

    pipe = list(RESTORE_ROOT.rglob("50-pipewire.conf"))
    exp = "/usr/share/alsa/alsa.conf.d/50-pipewire.conf"
    if pipe:
        got = os.readlink(pipe[0])
        checks.append(("50-pipewire.conf readlink", got == exp, f"got={got!r} expected={exp!r}"))
        checks.append(("50-pipewire.conf ist Symlink", pipe[0].is_symlink(), str(pipe[0])))
    else:
        checks.append(("50-pipewire.conf vorhanden", False, ""))

    awk = list(RESTORE_ROOT.rglob("awk"))
    awk = [p for p in awk if "alternatives" in str(p)]
    if awk:
        checks.append(("etc/alternatives/awk ist Symlink", awk[0].is_symlink(), str(awk[0])))
    else:
        checks.append(("etc/alternatives/awk vorhanden", False, ""))

    safe, why = _validate_containment(RESTORE_ROOT)
    checks.append(("alle Pfadknoten (ohne Symlink-Ziel-Auflösung) unter Restore-Wurzel", safe, why or ""))

    report = {
        "archive": str(archive_path),
        "restore_target": str(RESTORE_ROOT),
        "allowlist": [str(p) for p in ALLOW_PREFIXES],
        "checks": [{"name": n, "ok": o, "detail": d} for n, o, d in checks],
    }
    out_json = RESTORE_ROOT.parent / "setuphelfer-restore-test-report.json"
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(out_json.read_text(encoding="utf-8"))

    if not all(c[1] for c in checks):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
