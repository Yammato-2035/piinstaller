"""
Update-Center: Kompatibilitäts-Gate für DEB-Build und Release-Freigabe.

Regel A – Systembasis: unterstütztes Linux/Debian/Raspberry Pi OS.
Regel B – Abhängigkeiten: Python, Node/npm, Build-Tooling.
Regel C – Versionskonsistenz: VERSION, config/version.json, package.json, debian/changelog.
Regel D – Sicherheitsstatus: keine offenen ROT-Blocker (aus Kompatibilitätsprüfung abgeleitet).
Regel E – Packaging: debian/ vorhanden, Build-Skript nachvollziehbar.

DEB-Build darf nur freigegeben werden, wenn ready_for_deb_release True ist.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# Unterstützte OS-IDs für Regel A (Debian/Raspberry Pi OS)
SUPPORTED_OS_IDS = {"debian", "raspbian", "rpi"}
MIN_PYTHON_MAJOR, MIN_PYTHON_MINOR = 3, 9
HISTORY_FILE_NAME = "update_center_history.json"
HISTORY_MAX_ENTRIES = 20


def get_repo_root() -> Path:
    """Repository-Root (Eltern von backend/)."""
    return Path(__file__).resolve().parent.parent


def _read_text(path: Path, default: str = "") -> str:
    try:
        if path.is_file():
            return path.read_text(encoding="utf-8").strip()
    except Exception:
        pass
    return default


def read_os_release() -> dict[str, str]:
    """Liest /etc/os-release; leeres Dict wenn nicht vorhanden."""
    out: dict[str, str] = {}
    p = Path("/etc/os-release")
    if not p.is_file():
        return out
    raw = _read_text(p)
    for line in raw.splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            v = v.strip().strip('"').replace('\\"', '"')
            out[k] = v
    return out


def check_os_basis() -> tuple[bool, str, list[str]]:
    """Regel A: Unterstütztes Linux/Debian/Raspberry Pi OS. Returns (ok, summary, blockers)."""
    rel = read_os_release()
    name = rel.get("NAME", "").lower()
    id_like = rel.get("ID_LIKE", "").lower()
    pid = rel.get("ID", "").lower()
    version_id = rel.get("VERSION_ID", "")
    pretty = rel.get("PRETTY_NAME", name or "Unbekannt")

    ids = {pid, name, *id_like.replace(" ", "").split()}
    if not ids:
        return False, f"OS nicht erkennbar ({pretty})", ["Betriebssystem nicht erkannt (kein /etc/os-release oder ID)."]
    supported = bool(ids & SUPPORTED_OS_IDS)
    os_summary = f"{pretty} (ID={pid}, VERSION_ID={version_id})"
    if not supported:
        return False, os_summary, [f"Unterstützt werden nur Debian/Raspberry Pi OS; erkannt: {pretty}."]
    return True, os_summary, []


def check_python() -> tuple[bool, str, list[str]]:
    """Regel B: Python-Version im unterstützten Bereich."""
    v = sys.version_info
    if v.major < MIN_PYTHON_MAJOR or (v.major == MIN_PYTHON_MAJOR and v.minor < MIN_PYTHON_MINOR):
        return False, f"{v.major}.{v.minor}", [f"Python {v.major}.{v.minor} wird nicht unterstützt (mind. {MIN_PYTHON_MAJOR}.{MIN_PYTHON_MINOR})."]
    return True, f"{v.major}.{v.minor}", []


def check_node() -> tuple[bool, str, list[str]]:
    """Regel B: Node vorhanden (optional für Build). Kein Blocker, nur Warnung wenn fehlt."""
    try:
        r = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(get_repo_root()),
        )
        if r.returncode != 0 or not r.stdout:
            return False, "nicht gefunden", []
        # "v18.0.0" -> 18
        m = re.search(r"v?(\d+)\.", r.stdout.strip())
        major = int(m.group(1)) if m else 0
        if major < 18:
            return False, r.stdout.strip(), [f"Node-Version {r.stdout.strip()} möglicherweise zu alt (empfohlen 18+)."]
        return True, r.stdout.strip(), []
    except FileNotFoundError:
        return False, "nicht installiert", []
    except Exception:
        return False, "Prüfung fehlgeschlagen", []


def check_debian_structure(repo_root: Path) -> tuple[bool, str, list[str]]:
    """Regel E: debian/ vorhanden, control, rules; Build-Skript."""
    blockers: list[str] = []
    debian = repo_root / "debian"
    if not debian.is_dir():
        blockers.append("debian/ Verzeichnis fehlt.")
        return False, "debian/ fehlt", blockers
    if not (debian / "control").is_file():
        blockers.append("debian/control fehlt.")
    if not (debian / "rules").is_file():
        blockers.append("debian/rules fehlt.")
    build_script = repo_root / "scripts" / "build-deb.sh"
    if not build_script.is_file():
        blockers.append("scripts/build-deb.sh fehlt.")
    summary = "debian/ und Build-Skript vorhanden" if not blockers else "Struktur unvollständig"
    return len(blockers) == 0, summary, blockers


def get_version_from_json(path: Path) -> str | None:
    """Liest version aus JSON-Datei (config/version.json oder package.json)."""
    raw = _read_text(path)
    if not raw:
        return None
    try:
        data = json.loads(raw)
        if isinstance(data.get("version"), str):
            return data["version"].strip()
    except Exception:
        pass
    return None


def check_version_consistency(repo_root: Path) -> tuple[bool, dict[str, Any], list[str]]:
    """Regel C: VERSION, config/version.json, frontend/package.json, debian/changelog (erste Zeile)."""
    blockers: list[str] = []
    versions: dict[str, str] = {}

    vfile = repo_root / "VERSION"
    if vfile.is_file():
        versions["VERSION"] = _read_text(vfile).splitlines()[0].strip()
    else:
        versions["VERSION"] = ""

    version_json = repo_root / "config" / "version.json"
    versions["config/version.json"] = get_version_from_json(version_json) or ""

    pkg = repo_root / "frontend" / "package.json"
    versions["frontend/package.json"] = get_version_from_json(pkg) or ""

    changelog = repo_root / "debian" / "changelog"
    deb_ver = ""
    if changelog.is_file():
        first = _read_text(changelog).splitlines()[0]
        # pi-installer (1.3.4.15-1) unstable; ...
        m = re.search(r"\(([^)]+)\)", first)
        if m:
            deb_ver = m.group(1).strip()
    versions["debian/changelog"] = deb_ver

    canonical = versions.get("config/version.json") or versions.get("VERSION") or ""
    if not canonical:
        blockers.append("Keine kanonische Version (config/version.json oder VERSION) gefunden.")

    for name, val in versions.items():
        if val and canonical and val != canonical:
            # debian/changelog kann "1.3.4.15-1" sein, canonical "1.3.4.15"
            if name == "debian/changelog" and val.startswith(canonical):
                continue
            blockers.append(f"Versionskonflikt: {name} = {val!r}, erwartet {canonical!r}.")

    version_consistency = {
        "versions": versions,
        "canonical": canonical,
        "consistent": len(blockers) == 0,
    }
    return len(blockers) == 0, version_consistency, blockers


def run_compatibility_checks() -> dict[str, Any]:
    """
    Führt alle Gate-Prüfungen aus. Kein Build, nur Prüfung.
    Returns: checks_passed, warnings, blockers, os_summary, package_summary, dependency_summary,
             version_consistency, ready_for_deb_release.
    """
    repo_root = get_repo_root()
    warnings: list[str] = []
    blockers: list[str] = []

    # Regel A
    ok_a, os_summary, blk_a = check_os_basis()
    if not ok_a:
        blockers.extend(blk_a)

    # Regel B
    ok_py, py_ver, blk_py = check_python()
    if not ok_py:
        blockers.extend(blk_py)
    ok_node, node_ver, blk_node = check_node()
    if not ok_node and blk_node:
        blockers.extend(blk_node)
    elif not ok_node:
        warnings.append("Node nicht gefunden oder Version < 18 – Frontend-Build möglicherweise nicht möglich.")
    dependency_summary = f"Python {py_ver}, Node {node_ver}"

    # Regel C
    ok_c, version_consistency, blk_c = check_version_consistency(repo_root)
    if not ok_c:
        blockers.extend(blk_c)

    # Regel D: Keine zusätzlichen ROT-Blocker (aus diesem Check abgeleitet; externe Checkliste nicht angebunden)
    # Wenn alle anderen Regeln passen, gilt D als erfüllt.

    # Regel E
    ok_e, package_summary, blk_e = check_debian_structure(repo_root)
    if not ok_e:
        blockers.extend(blk_e)

    checks_passed = len(blockers) == 0
    ready_for_deb_release = checks_passed

    return {
        "checks_passed": checks_passed,
        "warnings": warnings,
        "blockers": blockers,
        "os_summary": os_summary,
        "package_summary": package_summary,
        "dependency_summary": dependency_summary,
        "version_consistency": version_consistency,
        "ready_for_deb_release": ready_for_deb_release,
    }


def append_history(entry: dict[str, Any]) -> None:
    """Hängt einen Eintrag an die Update-Center-History an (prüfen oder build)."""
    repo_root = get_repo_root()
    log_dir = repo_root / "logs"
    path = log_dir / HISTORY_FILE_NAME
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
        else:
            data = {"entries": []}
        data["entries"] = (data.get("entries") or [])[: (HISTORY_MAX_ENTRIES - 1)]
        data["entries"].insert(0, entry)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def get_history() -> list[dict[str, Any]]:
    """Liest die letzten Update-Center-Einträge."""
    path = get_repo_root() / "logs" / HISTORY_FILE_NAME
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("entries") or []
    except Exception:
        return []
