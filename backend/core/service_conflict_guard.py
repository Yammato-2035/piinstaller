"""
Erkennung paralleler pi-installer- vs. Setuphelfer-Installationen (Port 8000, systemd, Pfade).

Lesend: keine Prozessbeendigung, keine Datenlöschung.
Installer/postinst dürfen Legacy-Dienste kontrolliert stilllegen (siehe debian/postinst).
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Literal

from core.install_paths import DEFAULT_OPT, legacy_opt_live_path, path_text_suggests_legacy_pi_tree

logger = logging.getLogger(__name__)

LEGACY_SYSTEMD_UNITS = ("pi-installer.service", "pi-installer-backend.service")
SETUPHELFER_SYSTEMD_UNITS = ("setuphelfer-backend.service", "setuphelfer.service")

CONFLICT_LEGACY_PI_ACTIVE = "SERVICE-CONFLICT-033"
CONFLICT_PORT_WRONG_OWNER = "SERVICE-CONFLICT-034"
CONFLICT_MIXED_INSTALL = "SERVICE-CONFLICT-035"
CONFLICT_OLD_MUST_NOT_OVERWRITE_NEW = "SERVICE-CONFLICT-036"


def _parse_version_tuple(v: str) -> tuple[int, ...]:
    parts: list[int] = []
    for seg in (v or "").strip().split("."):
        if seg.isdigit():
            parts.append(int(seg))
        else:
            m = re.match(r"^(\d+)", seg)
            parts.append(int(m.group(1)) if m else 0)
    return tuple(parts) if parts else (0,)


def compare_versions(a: str, b: str) -> int:
    """-1 wenn a<b, 0 gleich, +1 wenn a>b."""
    ta, tb = _parse_version_tuple(a), _parse_version_tuple(b)
    maxlen = max(len(ta), len(tb))
    for i in range(maxlen):
        va = ta[i] if i < len(ta) else 0
        vb = tb[i] if i < len(tb) else 0
        if va < vb:
            return -1
        if va > vb:
            return 1
    return 0


def read_version_from_install_root(root: Path) -> str | None:
    """Liest config/version.json, sonst VERSION-Datei."""
    try:
        vj = root / "config" / "version.json"
        if vj.is_file():
            data = json.loads(vj.read_text(encoding="utf-8"))
            v = str(data.get("version") or "").strip()
            if v:
                return v
        vf = root / "VERSION"
        if vf.is_file():
            s = vf.read_text(encoding="utf-8").strip()
            return s or None
    except OSError:
        pass
    return None


def get_expected_install_root() -> Path:
    """Laufzeit-Installationswurzel (Repo-Root bzw. /opt/… über PI_INSTALLER_DIR)."""
    raw = (os.environ.get("SETUPHELFER_DIR") or os.environ.get("PI_INSTALLER_DIR") or "").strip()
    if raw:
        return Path(raw).resolve()
    return Path(__file__).resolve().parent.parent.parent


def detect_runtime_version() -> str:
    return read_version_from_install_root(get_expected_install_root()) or "0.0.0"


def _systemctl_is_active(unit: str) -> bool | None:
    """True/False, None wenn systemctl nicht verfügbar."""
    try:
        r = subprocess.run(
            ["systemctl", "is-active", unit],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode != 0:
            return False
        return r.stdout.strip() == "active"
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None


def _systemctl_is_enabled(unit: str) -> bool | None:
    try:
        r = subprocess.run(
            ["systemctl", "is-enabled", unit],
            capture_output=True,
            text=True,
            timeout=5,
        )
        out = r.stdout.strip().lower()
        if out in {"enabled", "enabled-runtime"}:
            return True
        if out in {"disabled", "masked", "static", "indirect"}:
            return False
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None


def detect_setuphelfer_services() -> dict[str, Any]:
    """systemd-Status für Legacy- und Setuphelfer-Units (nur lesend)."""
    out: dict[str, Any] = {"units": {}}
    for u in LEGACY_SYSTEMD_UNITS + SETUPHELFER_SYSTEMD_UNITS:
        act = _systemctl_is_active(u)
        en = _systemctl_is_enabled(u)
        out["units"][u] = {"active": act, "enabled": en}
    return out


def detect_installation_paths() -> dict[str, Any]:
    leg = legacy_opt_live_path()
    return {
        "legacy_opt": str(leg),
        "legacy_opt_exists": leg.is_dir(),
        "setuphelfer_opt": str(DEFAULT_OPT),
        "setuphelfer_opt_exists": DEFAULT_OPT.is_dir(),
        "expected_install_root": str(get_expected_install_root()),
        "legacy_version": read_version_from_install_root(leg) if leg.is_dir() else None,
        "setuphelfer_version_on_disk": read_version_from_install_root(DEFAULT_OPT) if DEFAULT_OPT.is_dir() else None,
    }


def _ss_pids_for_listen_port(port: int) -> list[int]:
    pids: list[int] = []
    try:
        r = subprocess.run(["ss", "-tlnp"], capture_output=True, text=True, timeout=5)
        if r.returncode != 0 or not r.stdout:
            return pids
        needle = f":{port}"
        for line in r.stdout.splitlines():
            if "LISTEN" not in line or needle not in line:
                continue
            for m in re.finditer(r"pid=(\d+)", line):
                try:
                    pids.append(int(m.group(1)))
                except ValueError:
                    pass
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return sorted(set(pids))


def _lsof_listen_pids(port: int) -> list[int]:
    pids: list[int] = []
    try:
        r = subprocess.run(
            ["lsof", "-i", f"TCP:{port}", "-sTCP:LISTEN", "-t"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode != 0 or not r.stdout.strip():
            return pids
        for line in r.stdout.strip().splitlines():
            try:
                pids.append(int(line.strip()))
            except ValueError:
                pass
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return sorted(set(pids))


def _pid_field(pid: int, name: str) -> str | None:
    try:
        p = Path(f"/proc/{pid}") / name
        if not p.exists():
            return None
        if name == "cmdline":
            raw = p.read_bytes()
            return raw.replace(b"\x00", b" ").decode("utf-8", errors="replace").strip() or None
        if name == "exe":
            return os.readlink(str(p))
        return p.read_text(encoding="utf-8", errors="replace").strip() or None
    except OSError:
        return None


def detect_port_owner(port: int = 8000) -> dict[str, Any]:
    pids = sorted(set(_ss_pids_for_listen_port(port) + _lsof_listen_pids(port)))
    owners: list[dict[str, Any]] = []
    for pid in pids:
        exe = _pid_field(pid, "exe")
        cmd = _pid_field(pid, "cmdline")
        cwd = _pid_field(pid, "cwd")
        owners.append({"pid": pid, "exe": exe, "cmdline": cmd, "cwd": cwd})
    return {"port": port, "listen_pids": pids, "owners": owners, "port_in_use": bool(pids)}


def _curl_local_version(port: int, timeout_s: float = 2.0) -> dict[str, Any]:
    try:
        import urllib.request

        url = f"http://127.0.0.1:{port}/api/version"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        data = json.loads(body)
        ver = str((data or {}).get("version") or "").strip()
        return {"reachable": True, "version": ver or None, "raw_status": data.get("status")}
    except Exception as e:
        return {"reachable": False, "error": str(e)[:500]}


@dataclass
class ServiceConflict:
    conflict_id: str
    detected_services: list[str] = field(default_factory=list)
    active_ports: dict[str, str] = field(default_factory=dict)
    active_versions: dict[str, str] = field(default_factory=dict)
    active_paths: list[str] = field(default_factory=list)
    severity: str = "high"
    recommended_action: str = ""
    safe_to_auto_disable: bool = False
    destructive_risk: bool = False
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


def classify_service_conflicts(port: int = 8000) -> list[ServiceConflict]:
    """Sammelt Konflikte (ohne Seiteneffekte)."""
    conflicts: list[ServiceConflict] = []
    services = detect_setuphelfer_services()
    paths = detect_installation_paths()
    port_info = detect_port_owner(port)
    expected = get_expected_install_root()
    runtime_ver = detect_runtime_version()

    legacy_units_active: list[str] = []
    sh_units_active: list[str] = []
    for u, st in services.get("units", {}).items():
        if st.get("active") is True:
            if u in LEGACY_SYSTEMD_UNITS:
                legacy_units_active.append(u)
            elif u in SETUPHELFER_SYSTEMD_UNITS:
                sh_units_active.append(u)

    owner_paths: list[str] = []
    for o in port_info.get("owners") or []:
        for k in ("exe", "cmdline", "cwd"):
            v = o.get(k)
            if isinstance(v, str) and v:
                owner_paths.append(v)

    # 036: Legacy-Start aus altem /opt-Baum, neuere Installation unter /opt/setuphelfer
    if expected.resolve() == legacy_opt_live_path().resolve():
        nv = paths.get("setuphelfer_version_on_disk")
        if DEFAULT_OPT.is_dir() and nv:
            if compare_versions(nv, runtime_ver) > 0:
                conflicts.append(
                    ServiceConflict(
                        conflict_id=CONFLICT_OLD_MUST_NOT_OVERWRITE_NEW,
                        detected_services=legacy_units_active,
                        active_versions={"runtime": runtime_ver, "opt_setuphelfer": nv},
                        active_paths=[str(expected), str(DEFAULT_OPT)],
                        severity="critical",
                        recommended_action=(
                            "Neuere Setuphelfer-Installation unter /opt/setuphelfer erkannt. "
                            "Diese alte Instanz nicht starten oder deployen; bitte nur setuphelfer-backend unter /opt/setuphelfer nutzen."
                        ),
                        safe_to_auto_disable=False,
                        destructive_risk=False,
                        notes="newer_on_disk_under_opt_setuphelfer",
                    )
                )

    # 033: Legacy-Dienst aktiv
    if legacy_units_active:
        conflicts.append(
            ServiceConflict(
                conflict_id=CONFLICT_LEGACY_PI_ACTIVE,
                detected_services=legacy_units_active,
                active_ports={str(port): "legacy_systemd_active"} if port_info.get("port_in_use") else {},
                active_versions={"runtime": runtime_ver},
                active_paths=[str(legacy_opt_live_path())] if paths.get("legacy_opt_exists") else [],
                severity="high",
                recommended_action=(
                    "sudo systemctl stop pi-installer.service pi-installer-backend.service; "
                    "sudo systemctl disable pi-installer.service pi-installer-backend.service"
                ),
                safe_to_auto_disable=True,
                destructive_risk=False,
                notes="legacy_systemd",
            )
        )

    # 034: Port belegt, Owner nicht diese Installation
    if port_info.get("port_in_use"):
        ours = str(expected.resolve())
        owner_is_us = any(ours in (p or "") for p in owner_paths)
        if not owner_is_us:
            api = _curl_local_version(port)
            wrong_leg = any(path_text_suggests_legacy_pi_tree(p or "") for p in owner_paths)
            if wrong_leg or (api.get("reachable") and not owner_is_us and legacy_units_active):
                conflicts.append(
                    ServiceConflict(
                        conflict_id=CONFLICT_PORT_WRONG_OWNER,
                        detected_services=legacy_units_active + sh_units_active,
                        active_ports={str(port): "listener_not_expected_install"},
                        active_versions={"api_on_port": str(api.get("version") or ""), "runtime": runtime_ver},
                        active_paths=owner_paths[:8],
                        severity="high",
                        recommended_action=(
                            "Prüfen: ss -tlnp | grep :8000; Prozess-Pfad prüfen. "
                            "Wenn pi-installer: sudo systemctl stop/disable pi-installer*. "
                            "Sonst setuphelfer-backend nach Freigabe von :8000 starten."
                        ),
                        safe_to_auto_disable=bool(legacy_units_active),
                        destructive_risk=False,
                        notes="port_owner_mismatch",
                    )
                )
            elif not owner_is_us and api.get("reachable"):
                # Listener nicht eindeutig zuordenbar, aber Port belegt — nur melden wenn nicht wir
                conflicts.append(
                    ServiceConflict(
                        conflict_id=CONFLICT_PORT_WRONG_OWNER,
                        detected_services=sh_units_active,
                        active_ports={str(port): "foreign_or_unknown_listener"},
                        active_versions={"api_on_port": str(api.get("version") or ""), "runtime": runtime_ver},
                        active_paths=owner_paths[:8],
                        severity="medium",
                        recommended_action="Port 8000 prüfen; anderen Dienst stoppen oder PI_INSTALLER_BACKEND_PORT setzen.",
                        safe_to_auto_disable=False,
                        destructive_risk=False,
                        notes="ambiguous_listener",
                    )
                )

    # 035: gemischte Installation (beide Bäume + Legacy-Dienst noch enabled/aktiv)
    if paths.get("legacy_opt_exists") and paths.get("setuphelfer_opt_exists"):
        leg_enabled = any(_systemctl_is_enabled(u) is True for u in LEGACY_SYSTEMD_UNITS)
        if leg_enabled or legacy_units_active:
            if not any(c.conflict_id == CONFLICT_MIXED_INSTALL for c in conflicts):
                conflicts.append(
                    ServiceConflict(
                        conflict_id=CONFLICT_MIXED_INSTALL,
                        detected_services=legacy_units_active + sh_units_active,
                        active_versions={
                            "legacy": str(paths.get("legacy_version") or ""),
                            "setuphelfer_disk": str(paths.get("setuphelfer_version_on_disk") or ""),
                            "runtime": runtime_ver,
                        },
                        active_paths=[str(legacy_opt_live_path()), str(DEFAULT_OPT)],
                        severity="medium",
                        recommended_action=(
                            "Nur ein Backend-Owner auf :8000; Legacy pi-installer stoppen/disable, "
                            "Setuphelfer unter /opt/setuphelfer nutzen. "
                            "Archivierte Legacy-Daten unter /opt nicht automatisch löschen."
                        ),
                        safe_to_auto_disable=True,
                        destructive_risk=False,
                        notes="both_opt_trees",
                    )
                )

    # Duplikat-IDs entfernen (gleiche ID nur einmal, höchste Severity behalten ist optional — hier merge by id)
    merged: dict[str, ServiceConflict] = {}
    for c in conflicts:
        if c.conflict_id not in merged:
            merged[c.conflict_id] = c
    return list(merged.values())


def recommended_resolution(conflict_id: str) -> str:
    for c in classify_service_conflicts():
        if c.conflict_id == conflict_id:
            return c.recommended_action
    return ""


def should_block_start(port: int = 8000) -> tuple[bool, str]:
    """
    True, wenn ein Start des aktuellen Codes riskant/falsch wäre (Legacy blockiert, Downgrade-Laufwerk).
    Kein Kill — nur Entscheidungshilfe für Skripte/__main__.
    """
    for c in classify_service_conflicts(port=port):
        if c.conflict_id == CONFLICT_OLD_MUST_NOT_OVERWRITE_NEW:
            return True, c.recommended_action
        if c.conflict_id == CONFLICT_LEGACY_PI_ACTIVE and detect_port_owner(port).get("port_in_use"):
            return True, c.recommended_action
        if c.conflict_id == CONFLICT_PORT_WRONG_OWNER and c.severity == "high":
            return True, c.recommended_action
    return False, ""


def build_service_conflict_report(port: int = 8000) -> dict[str, Any]:
    conflicts = classify_service_conflicts(port=port)
    block, reason = should_block_start(port=port)
    actions: list[str] = []
    for c in conflicts:
        if c.recommended_action:
            actions.append(f"[{c.conflict_id}] {c.recommended_action}")
    return {
        "conflicts": [c.as_dict() for c in conflicts],
        "active_services": detect_setuphelfer_services(),
        "port_owner": detect_port_owner(port),
        "runtime_version": detect_runtime_version(),
        "install_paths": detect_installation_paths(),
        "recommended_actions": actions,
        "should_block_start": block,
        "block_reason": reason,
    }


PortStartupDecision = Literal["proceed", "same_instance", "conflict", "unknown"]


def evaluate_port_before_bind(port: int) -> tuple[PortStartupDecision, str]:
    """
    Für start-backend.sh: Port frei → proceed; unser Stack lauscht bereits → same_instance;
    harter Konflikt (Legacy/ falscher Owner) → conflict; sonst unknown.
    """
    port_info = detect_port_owner(port)
    if not port_info.get("port_in_use"):
        return "proceed", ""

    expected = get_expected_install_root()
    ours = str(expected.resolve())
    owner_paths: list[str] = []
    for o in port_info.get("owners") or []:
        for k in ("exe", "cmdline", "cwd"):
            v = o.get(k)
            if isinstance(v, str) and v:
                owner_paths.append(v)

    api = _curl_local_version(port)
    runtime_ver = detect_runtime_version()

    if any(path_text_suggests_legacy_pi_tree(p or "") for p in owner_paths):
        return "conflict", (
            "Port %s wird von einem Prozess aus dem archivierten Legacy-Installationsbaum "
            "(historischer Ordner pi-installer unter /opt) belegt. "
            "sudo systemctl stop pi-installer.service pi-installer-backend.service && "
            "sudo systemctl disable pi-installer.service pi-installer-backend.service"
        ) % port

    legacy_active = any(_systemctl_is_active(u) is True for u in LEGACY_SYSTEMD_UNITS)
    if legacy_active:
        return "conflict", (
            "Legacy pi-installer-Dienst ist aktiv. "
            "sudo systemctl stop pi-installer.service pi-installer-backend.service && "
            "sudo systemctl disable pi-installer.service pi-installer-backend.service"
        )

    owner_is_us = any(ours in (p or "") for p in owner_paths)
    if owner_is_us and api.get("reachable") and api.get("version") == runtime_ver:
        return "same_instance", "Bereits dieser Setuphelfer-Stack auf dem Port aktiv."

    if api.get("reachable") and not owner_is_us:
        # Fremde API antwortet — nicht blind als „unser“ Backend akzeptieren
        return "conflict", (
            "Port %s belegt; /api/version antwortet, aber Listener gehört nicht zu PI_INSTALLER_DIR=%s. "
            "Listener prüfen (ss -tlnp) und ggf. falschen Dienst stoppen."
        ) % (port, ours)

    if owner_is_us:
        return "same_instance", "Listener-Pfad passt zur erwarteten Installation."

    return "unknown", "Port belegt; Owner nicht eindeutig — ss -tlnp / lsof prüfen."


def port_preflight_main() -> int:
    """
    CLI-Hilfe für start-backend.sh (stderr = Hinweise, Exit-Code):
    0 proceed, 10 same_instance (Skript soll exit 0), 2 conflict, 11 unknown.
    """
    import sys

    port = int(os.environ.get("PI_INSTALLER_BACKEND_PORT", "8000"))
    d, msg = evaluate_port_before_bind(port)
    if d == "same_instance":
        print(
            "ℹ️  Port %s ist belegt – es laeuft bereits dieser Setuphelfer-Stack (/api/version passt zum Installationspfad)."
            % port,
            file=sys.stderr,
        )
        if msg:
            print("   " + msg, file=sys.stderr)
        return 10
    if d == "conflict":
        print("❌ Service-/Port-Konflikt (Setuphelfer service_conflict_guard):", file=sys.stderr)
        print("   " + (msg or "Konflikt"), file=sys.stderr)
        return 2
    if d == "unknown" and msg:
        print("⚠️  " + msg, file=sys.stderr)
    return 0 if d == "proceed" else 11


def preflight_block_legacy_on_port(port: int) -> None:
    """Für __main__: bei Konflikt SystemExit mit kurzer Anleitung."""
    if (os.environ.get("SETUPHELFER_SKIP_SERVICE_CONFLICT_GUARD") or "").strip() in ("1", "true", "yes"):
        return
    if (os.environ.get("PI_INSTALLER_SKIP_SERVICE_CONFLICT_GUARD") or "").strip() in ("1", "true", "yes"):
        return
    os.environ["PI_INSTALLER_BACKEND_PORT"] = str(port)
    ec = port_preflight_main()
    if ec == 2:
        raise SystemExit(2)


def diagnostics_signals_for_matcher(port: int = 8000) -> dict[str, str]:
    """Flache Signale für DiagnosticsAnalyzeRequest / Matcher."""
    rep = build_service_conflict_report(port=port)
    sig: dict[str, str] = {}
    ids = [c["conflict_id"] for c in rep.get("conflicts") or []]
    sig["service_conflict_ids"] = ",".join(ids)
    po = rep.get("port_owner") or {}
    owners = po.get("owners") or []
    joined = " ".join(
        str(x)
        for o in owners
        for x in (o.get("exe"), o.get("cmdline"))
        if x
    ).lower()
    sig["port_8000_owner_text"] = joined[:4000]
    for u, st in (rep.get("active_services") or {}).get("units", {}).items():
        safe = "systemd_" + u.replace(".", "_").replace("-", "_")
        sig[safe] = "active" if st.get("active") is True else "inactive"
    ip = rep.get("install_paths") or {}
    sig["mixed_opt_install"] = "true" if ip.get("legacy_opt_exists") and ip.get("setuphelfer_opt_exists") else "false"
    sig["runtime_version"] = (rep.get("runtime_version") or "").lower()
    sig["setuphelfer_version_on_disk"] = str(ip.get("setuphelfer_version_on_disk") or "").lower()
    sig["legacy_systemd_still_enabled"] = (
        "true"
        if any(_systemctl_is_enabled(u) is True for u in LEGACY_SYSTEMD_UNITS)
        else "false"
    )
    if any(c.get("conflict_id") == CONFLICT_OLD_MUST_NOT_OVERWRITE_NEW for c in (rep.get("conflicts") or [])):
        sig["legacy_must_not_overwrite_new"] = "true"
    return sig
