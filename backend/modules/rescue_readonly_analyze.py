"""
Orchestrierung der Read-only-Rescue-Analyse (Speicher, SMART, FS, Boot, Netz).

Schreibt den JSON-Bericht nach ``/tmp/setuphelfer-rescue-report.json``.
"""

from __future__ import annotations

import json
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from models.diagnosis import RescueAnalyzeResponse, RescueFinding, RescueRiskLevel

from modules.inspect_boot import analyze_boot_status
from modules.inspect_storage import (
    check_mountability,
    detect_filesystems,
    detect_uuid_conflicts,
    list_block_devices,
    list_physical_disks,
    readonly_fs_check,
    read_partition_table,
    smart_classify_disk,
)

Runner = Callable[..., subprocess.CompletedProcess[str]]

REPORT_JSON = Path("/tmp/setuphelfer-rescue-report.json")
REPORT_MD = Path("/tmp/setuphelfer-rescue-report.md")


def _run_capture(
    argv: list[str],
    *,
    runner: Runner | None = None,
    timeout: int = 30,
) -> subprocess.CompletedProcess[str]:
    run = runner or subprocess.run
    return run(argv, capture_output=True, text=True, timeout=timeout, check=False)


def _risk_for_finding_code(code: str) -> RescueRiskLevel:
    """Ampel je stabilem Code (unbekannte rescue.*-Codes konservativ: yellow)."""
    table: dict[str, RescueRiskLevel] = {
        "rescue.storage.duplicate_uuid": "red",
        "rescue.storage.partition_table_unreadable": "yellow",
        "rescue.storage.lsblk_empty": "yellow",
        "rescue.storage.findmnt_json_invalid": "yellow",
        "rescue.storage.mounted_read_write": "yellow",
        "rescue.storage.mounted_inspected": "green",
        "rescue.storage.partition_table_ok": "green",
        "rescue.storage.partition_table_ok_fdisk": "green",
        "rescue.smart.critical": "red",
        "rescue.smart.warning": "yellow",
        "rescue.smart.ok": "green",
        "rescue.smart.not_available": "yellow",
        "rescue.smart.command_failed": "yellow",
        "rescue.smart.invalid_device": "yellow",
        "rescue.fs.fsck_error": "red",
        "rescue.fs.fsck_issues": "yellow",
        "rescue.fs.fsck_ok": "green",
        "rescue.fs.xfs_repair_error": "red",
        "rescue.fs.xfs_repair_issues": "yellow",
        "rescue.fs.xfs_repair_ok": "green",
        "rescue.fs.skipped_mounted": "yellow",
        "rescue.fs.unsupported_or_unknown_fstype": "yellow",
        "rescue.boot.kernel_missing": "red",
        "rescue.boot.initrd_missing": "yellow",
        "rescue.boot.boot_dir_missing": "red",
        "rescue.boot.fstab_missing": "yellow",
        "rescue.boot.fstab_unreadable": "yellow",
        "rescue.boot.fstab_parse_error": "yellow",
        "rescue.boot.layout_ok": "green",
        "rescue.network.no_interfaces": "yellow",
        "rescue.network.no_ipv4": "yellow",
        "rescue.network.ipv4_ok": "green",
        "rescue.network.gateway_unreachable": "yellow",
        "rescue.network.gateway_ok": "green",
        "rescue.network.psutil_missing": "yellow",
        "rescue.internal.error": "red",
    }
    if code in table:
        return table[code]
    if code.startswith("rescue.") and code.endswith("_ok"):
        return "green"
    return "yellow"


def _max_risk(levels: list[RescueRiskLevel]) -> RescueRiskLevel:
    if "red" in levels:
        return "red"
    if "yellow" in levels:
        return "yellow"
    return "green"


def _append_finding(
    findings: list[RescueFinding],
    *,
    code: str,
    area: str,
    evidence: dict[str, Any] | None = None,
) -> None:
    findings.append(
        RescueFinding(
            code=code,
            area=area,
            risk_level=_risk_for_finding_code(code),
            evidence=evidence or {},
        )
    )


def _analyze_network(*, runner: Runner | None = None) -> dict[str, Any]:
    try:
        import psutil
    except ImportError:
        return {
            "interfaces": [],
            "ipv4": [],
            "gateway": None,
            "gateway_reachable": None,
            "code": "rescue.network.psutil_missing",
        }
    ifaces = psutil.net_if_addrs()
    names = sorted(ifaces.keys())
    ipv4_rows: list[dict[str, str]] = []
    for name in names:
        for addr in ifaces.get(name, []):
            if addr.family == socket.AF_INET:
                ip = addr.address
                if ip and not ip.startswith("127."):
                    ipv4_rows.append({"interface": name, "address": ip})
    gw = None
    r = _run_capture(["ip", "-j", "route", "show", "default"], runner=runner, timeout=15)
    if r.returncode == 0 and (r.stdout or "").strip():
        try:
            data = json.loads(r.stdout or "[]")
            if isinstance(data, list) and data:
                g = data[0].get("gateway")
                if isinstance(g, str) and g:
                    gw = g
        except json.JSONDecodeError:
            pass
    reachable: bool | None = None
    if gw:
        ping = _run_capture(
            ["ping", "-c", "1", "-W", "2", gw],
            runner=runner,
            timeout=10,
        )
        reachable = ping.returncode == 0
    return {
        "interfaces": names,
        "ipv4": ipv4_rows,
        "gateway": gw,
        "gateway_reachable": reachable,
        "code": "rescue.network.summary",
    }


def run_rescue_readonly_analysis(
    *,
    root: Path | str = "/",
    runner: Runner | None = None,
    write_reports: bool = True,
) -> RescueAnalyzeResponse:
    try:
        return _run_rescue_readonly_analysis_impl(
            root=root,
            runner=runner,
            write_reports=write_reports,
        )
    except Exception as exc:  # pragma: no cover - Abfang für unerwartete Systemfehler
        resp = RescueAnalyzeResponse(
            status="error",
            risk_level="red",
            findings=[
                RescueFinding(
                    code="rescue.internal.error",
                    area="internal",
                    risk_level="red",
                    evidence={"error_type": type(exc).__name__},
                )
            ],
            devices=[],
            boot_status={},
            network_status={},
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
        if write_reports:
            try:
                REPORT_JSON.write_text(resp.model_dump_json(indent=2), encoding="utf-8")
            except OSError:
                pass
        return resp


def _run_rescue_readonly_analysis_impl(
    *,
    root: Path | str = "/",
    runner: Runner | None = None,
    write_reports: bool = True,
) -> RescueAnalyzeResponse:
    findings: list[RescueFinding] = []
    devices = list_block_devices(runner=runner)
    if not devices:
        _append_finding(findings, code="rescue.storage.lsblk_empty", area="storage", evidence={})

    uuid_info = detect_uuid_conflicts(runner=runner)
    if uuid_info.get("has_conflicts"):
        _append_finding(
            findings,
            code="rescue.storage.duplicate_uuid",
            area="storage",
            evidence={"conflicts": uuid_info.get("conflicts")},
        )

    mount_rows = check_mountability(read_only=True, runner=runner)
    for row in mount_rows:
        if row.get("policy_code") == "rescue.storage.findmnt_json_invalid":
            _append_finding(
                findings,
                code="rescue.storage.findmnt_json_invalid",
                area="storage",
                evidence={"device": row.get("device")},
            )
        elif row.get("mounted") and row.get("readonly_effective") is False:
            _append_finding(
                findings,
                code="rescue.storage.mounted_read_write",
                area="storage",
                evidence={"device": row.get("device"), "mountpoint": row.get("mountpoint")},
            )

    fs_map = detect_filesystems(runner=runner)
    disks = list_physical_disks(runner=runner)
    if disks:
        smart_rows = [(d, smart_classify_disk(d, runner=runner)) for d in disks]
        if all(str(s.get("risk_code")) == "rescue.smart.not_available" for _, s in smart_rows):
            _append_finding(
                findings,
                code="rescue.smart.not_available",
                area="smart",
                evidence={"disk_count": len(disks)},
            )
        else:
            for d, sm in smart_rows:
                code = str(sm.get("risk_code") or "rescue.smart.not_available")
                if code == "rescue.smart.ok":
                    continue
                _append_finding(
                    findings,
                    code=code,
                    area="smart",
                    evidence={"device": d, "state": sm.get("state")},
                )

    for dev, meta in fs_map.items():
        fst = meta.get("type")
        chk = readonly_fs_check(dev, fst, runner=runner)
        c = chk.get("code")
        if isinstance(c, str):
            if c == "rescue.fs.fsck_ok" or c == "rescue.fs.xfs_repair_ok":
                continue
            _append_finding(findings, code=c, area="filesystem", evidence={"device": dev, "fstype": fst})

    for d in disks:
        pt = read_partition_table(d, runner=runner)
        pc = pt.get("code")
        if pc == "rescue.storage.partition_table_unreadable":
            _append_finding(
                findings,
                code=str(pc),
                area="storage",
                evidence={"disk": pt.get("disk"), "source": pt.get("source")},
            )

    boot_status = analyze_boot_status(root, runner=runner)
    codes = list(boot_status.get("codes") or [])
    if "rescue.boot.layout_ok" in codes and any(
        x in codes
        for x in (
            "rescue.boot.kernel_missing",
            "rescue.boot.boot_dir_missing",
            "rescue.boot.fstab_missing",
            "rescue.boot.fstab_unreadable",
            "rescue.boot.fstab_parse_error",
            "rescue.boot.initrd_missing",
        )
    ):
        codes.remove("rescue.boot.layout_ok")
    for c in codes:
        if c == "rescue.boot.layout_ok":
            _append_finding(
                findings,
                code=c,
                area="boot",
                evidence={"primary_boot": boot_status.get("primary_boot")},
            )
            continue
        ev = {k: boot_status[k] for k in ("fstab_code", "primary_boot", "fstab_lines") if k in boot_status}
        _append_finding(findings, code=c, area="boot", evidence=ev)

    net = _analyze_network(runner=runner)
    if net.get("code") == "rescue.network.psutil_missing":
        _append_finding(findings, code="rescue.network.psutil_missing", area="network", evidence={})
    elif not net.get("interfaces"):
        _append_finding(findings, code="rescue.network.no_interfaces", area="network", evidence={})
    elif not net.get("ipv4"):
        _append_finding(findings, code="rescue.network.no_ipv4", area="network", evidence={})
    else:
        _append_finding(
            findings,
            code="rescue.network.ipv4_ok",
            area="network",
            evidence={"count": len(net["ipv4"])},
        )
    if net.get("gateway") and net.get("gateway_reachable") is False:
        _append_finding(
            findings,
            code="rescue.network.gateway_unreachable",
            area="network",
            evidence={"gateway": net.get("gateway")},
        )
    elif net.get("gateway") and net.get("gateway_reachable") is True:
        _append_finding(
            findings,
            code="rescue.network.gateway_ok",
            area="network",
            evidence={"gateway": net.get("gateway")},
        )

    levels = [f.risk_level for f in findings] or ["green"]
    risk = _max_risk(levels)

    resp = RescueAnalyzeResponse(
        status="ok",
        risk_level=risk,
        findings=findings,
        devices=devices,
        boot_status=boot_status,
        network_status=net,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )

    if write_reports:
        try:
            REPORT_JSON.write_text(resp.model_dump_json(indent=2), encoding="utf-8")
        except OSError:
            pass
        try:
            lines = [
                "# Setuphelfer Rescue Report",
                "",
                f"risk_level: {risk}",
                "",
                "## Findings",
            ]
            for f in findings:
                lines.append(f"- `{f.code}` ({f.risk_level}) area={f.area}")
            REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
        except OSError:
            pass

    return resp


__all__ = ["REPORT_JSON", "REPORT_MD", "run_rescue_readonly_analysis"]
