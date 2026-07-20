"""PI-RS-TUI-AUTO-001 — automated TUI input diagnostic orchestrator."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable

from core.rescue_tui_input_diagnostic_contract import (
    DiagnosticConfig,
    DiagnosticResult,
    blocked_tui_actions,
    config_from_cmdline,
    default_run_id,
    diagnostic_mode_enabled,
    write_guard_response,
)
from core.rescue_tui_input_diagnostic_evaluate import (
    analyze_fds,
    classify_cpu,
    evaluate_tui_input_diagnostic,
)
from core.rescue_tui_input_diagnostic_evidence import (
    assert_path_under_allowed_roots,
    atomic_write_json,
    atomic_write_text,
    finalize_run_dir,
)
from core.rescue_tui_input_diagnostic_evdev import PassiveEvdevMonitor, event_to_dict
from core.rescue_tui_input_diagnostic_inventory import inventory_from_proc_devices
from core.rescue_tui_input_diagnostic_persistence import (
    build_diagnostic_shutdown_decision,
    complete_diagnostic_persistence,
    maybe_cleanup_runtime,
    resolve_runtime_evidence_root,
)

def resolve_whiptail_pids(
    *,
    systemctl_show: Callable[[], str] | None = None,
    ps_output: str | None = None,
) -> dict[str, Any]:
    main_pid = ""
    if systemctl_show is None:
        try:
            proc = subprocess.run(
                ["systemctl", "show", "setuphelfer-rescue-tui.service", "-p", "MainPID", "--value"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            main_pid = (proc.stdout or "").strip()
        except (OSError, subprocess.TimeoutExpired):
            main_pid = ""
    else:
        main_pid = systemctl_show().strip()

    if ps_output is None:
        try:
            proc = subprocess.run(
                ["ps", "-eo", "pid,ppid,tty,stat,pcpu,cmd"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            ps_output = proc.stdout or ""
        except (OSError, subprocess.TimeoutExpired):
            ps_output = ""

    whiptails: list[dict[str, Any]] = []
    for line in ps_output.splitlines():
        if "whiptail" not in line or "grep" in line:
            continue
        parts = line.split(None, 5)
        if len(parts) < 6:
            continue
        whiptails.append(
            {
                "pid": parts[0],
                "ppid": parts[1],
                "tty": parts[2],
                "stat": parts[3],
                "pcpu": parts[4],
                "cmd": parts[5],
            }
        )

    status = "ok"
    selected = None
    if len(whiptails) > 1:
        status = "multiple_whiptail_instances"
        # Prefer child of MainPID tree when possible
        if main_pid and main_pid != "0":
            for w in whiptails:
                if w["ppid"] == main_pid or _is_descendant(w["pid"], main_pid):
                    selected = w
                    break
        if selected is None:
            selected = None
    elif len(whiptails) == 1:
        selected = whiptails[0]
    return {
        "main_pid": main_pid,
        "instances": whiptails,
        "selected": selected,
        "status": status if whiptails else "not_found",
    }


def _is_descendant(pid: str, ancestor: str) -> bool:
    """Best-effort PPID walk via /proc."""
    cur = pid
    for _ in range(32):
        try:
            stat = Path(f"/proc/{cur}/stat").read_text(encoding="utf-8", errors="replace")
        except OSError:
            return False
        # pid (comm) state ppid ...
        m = re.match(r"^\d+ \(.*\) . (\d+)", stat)
        if not m:
            return False
        ppid = m.group(1)
        if ppid == ancestor:
            return True
        if ppid in {"0", "1"}:
            return False
        cur = ppid
    return False


def read_proc_fd(pid: str, fd: int) -> str:
    try:
        return os.readlink(f"/proc/{pid}/fd/{fd}")
    except OSError:
        return ""


def sample_cpu(pid: str, *, samples: int = 15, interval_s: float = 1.0) -> dict[str, Any]:
    """Sample /proc/<pid>/stat utime+stime deltas vs wall clock (approx % of one core)."""
    rows: list[dict[str, Any]] = []
    prev = _read_cpu_times(pid)
    prev_wall = time.monotonic()
    hz = os.sysconf(os.sysconf_names.get("SC_CLK_TCK", "SC_CLK_TCK")) if hasattr(os, "sysconf") else 100
    try:
        hz = int(hz)
    except (TypeError, ValueError):
        hz = 100

    for i in range(max(1, samples)):
        time.sleep(max(0.05, interval_s))
        cur = _read_cpu_times(pid)
        wall = time.monotonic()
        if prev and cur:
            dt = max(1e-6, wall - prev_wall)
            d_ticks = (cur["utime"] + cur["stime"]) - (prev["utime"] + prev["stime"])
            pct = max(0.0, (d_ticks / hz) / dt * 100.0)
        else:
            pct = 0.0
        wchan = ""
        try:
            wchan = Path(f"/proc/{pid}/wchan").read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            pass
        state = (cur or {}).get("state", "?")
        rows.append({"sample": i + 1, "pcpu": round(pct, 2), "state": state, "wchan": wchan})
        prev = cur
        prev_wall = wall

    vals = [r["pcpu"] for r in rows]
    avg = sum(vals) / len(vals) if vals else 0.0
    return {
        "samples": rows,
        "cpu_avg_percent": round(avg, 2),
        "cpu_max_percent": round(max(vals) if vals else 0.0, 2),
        "cpu_class": classify_cpu(avg),
    }


def _read_cpu_times(pid: str) -> dict[str, Any] | None:
    try:
        raw = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    # comm can contain spaces/parens — split after last ')'
    try:
        rest = raw[raw.rfind(")") + 2 :].split()
        state = rest[0]
        utime = int(rest[11])
        stime = int(rest[12])
    except (IndexError, ValueError):
        return None
    return {"state": state, "utime": utime, "stime": stime}


def parse_stty_a(text: str) -> dict[str, Any]:
    flags = set(re.findall(r"(?<![-\w])(-?[a-z0-9]+)(?![=\w])", text))
    # stty -a uses "echo" or "-echo"
    def has(name: str) -> bool:
        if f"-{name}" in text.split():
            return False
        return bool(re.search(rf"(?<![-\w]){name}(?![-\w])", text))

    rows = None
    cols = None
    m = re.search(r"rows\s+(\d+).*columns\s+(\d+)", text)
    if m:
        rows, cols = int(m.group(1)), int(m.group(2))
    icanon = has("icanon")
    echo = has("echo")
    raw_mode = (not icanon) and (not echo)
    suspicious: list[str] = []
    if raw_mode:
        suspicious.append("raw_or_noncanonical_noecho")
    if not has("isig"):
        suspicious.append("-isig")
    return {
        "term": os.environ.get("TERM", ""),
        "rows": rows,
        "columns": cols,
        "icanon": icanon,
        "echo": echo,
        "isig": has("isig"),
        "ixon": has("ixon"),
        "opost": has("opost"),
        "raw_mode_detected": raw_mode,
        "suspicious_flags": suspicious,
        "raw_stty": text[:2000],
    }


def read_tty1_state(tty_path: str = "/dev/tty1") -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["stty", "-a"],
            stdin=open(tty_path, "rb", buffering=0),  # noqa: SIM115 — intentional tty open
            capture_output=True,
            text=True,
            check=False,
            timeout=3,
        )
        text = (proc.stdout or "") + (proc.stderr or "")
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "unreadable", "error": str(exc)}
    parsed = parse_stty_a(text)
    parsed["status"] = "ok"
    return parsed


def collect_tty1_owners(ps_output: str | None = None) -> dict[str, Any]:
    if ps_output is None:
        try:
            proc = subprocess.run(
                ["ps", "-eo", "pid,ppid,tty,stat,pcpu,cmd"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            ps_output = proc.stdout or ""
        except (OSError, subprocess.TimeoutExpired):
            ps_output = ""
    owners = []
    for line in ps_output.splitlines():
        parts = line.split(None, 5)
        if len(parts) < 6:
            continue
        if parts[2] == "tty1" or any(
            k in parts[5] for k in ("boot-progress", "whiptail", "setuphelfer-rescue-tui", "agetty", "getty@tty1")
        ):
            owners.append({"pid": parts[0], "tty": parts[2], "cmd": parts[5][:200]})
    # competition if more than tui+whiptail writers
    cmds = " ".join(o["cmd"] for o in owners)
    competing = ("boot-progress" in cmds) or ("agetty" in cmds and "whiptail" in cmds)
    return {
        "tty1_owners": owners,
        "competing_writer_detected": competing,
        "severity": "possible" if competing else "none",
    }


def try_screen_dump(vt: int, dest: Path) -> dict[str, Any]:
    if not shutil.which("setterm"):
        return {"screen_dump_status": "unavailable", "reason": "setterm_not_found"}
    # Prefer dump-only invocation; never --reset/--initialize
    try:
        proc = subprocess.run(
            ["setterm", "--dump", str(vt), "--file", str(dest)],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"screen_dump_status": "unavailable", "reason": str(exc)}
    if proc.returncode != 0 or not dest.is_file():
        return {
            "screen_dump_status": "unavailable",
            "reason": (proc.stderr or proc.stdout or "dump_failed")[:200],
        }
    return {"screen_dump_status": "ok", "path": str(dest), "size": dest.stat().st_size}


def chvt_safe(vt: int) -> dict[str, Any]:
    if not shutil.which("chvt"):
        return {"ok": False, "reason": "chvt_missing"}
    try:
        proc = subprocess.run(["chvt", str(vt)], capture_output=True, text=True, check=False, timeout=5)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "reason": str(exc)}
    return {"ok": proc.returncode == 0, "rc": proc.returncode}


def resolve_evidence_root(config: DiagnosticConfig) -> Path:
    """Always use a runtime working root; SETUP_LOGS persistence happens at finalize."""
    if config.evidence_root is not None:
        root = Path(config.evidence_root)
        # Treat explicit CLI/test evidence_root as the runtime parent.
        if str(root) not in {"", "."}:
            root.mkdir(parents=True, exist_ok=True)
            return root
    return resolve_runtime_evidence_root()


def _apply_persistence(
    config: DiagnosticConfig,
    result: DiagnosticResult,
    run_dir: Path,
    *,
    resolver: Any = None,
) -> None:
    """Finalize runtime evidence onto SETUP_LOGS with a bounded mount wait."""
    result.runtime_path = str(run_dir)
    if not config.enable_persistence:
        result.persistence_status = "runtime_only"
        result.shutdown_allowed = False
        return
    published = complete_diagnostic_persistence(
        runtime_run_dir=run_dir,
        run_id=config.run_id,
        timeout_s=float(config.persist_timeout_s),
        interval_s=float(config.persist_interval_s),
        allow_safe_mount=True,
        resolver=resolver,
        runtime_override=Path(config.evidence_root) if config.evidence_root else None,
    )
    result.persistence_status = published.status
    result.persistent_path = published.persistent_path
    result.shutdown_allowed = published.shutdown_allowed
    decision = build_diagnostic_shutdown_decision(published)
    _diag_print(config, decision.operator_message_de)
    _diag_print(
        config,
        "\n".join(
            [
                "Laufdaten werden temporär erfasst: ja",
                f"SETUP_LOGS gefunden: {'ja' if published.persistent_path else 'nein'}",
                f"Persistente Speicherung: {decision.persistence_status}",
                f"Herunterfahren erlaubt: {'ja' if decision.shutdown_allowed else 'nein'}",
            ]
        ),
    )
    if published.runtime_cleanup_allowed:
        maybe_cleanup_runtime(run_dir, published)
    if config.auto_shutdown:
        if decision.shutdown_allowed:
            _diag_print(config, "Auto-Shutdown freigegeben (Persistenz bestätigt).")
            try:
                subprocess.run(["systemctl", "poweroff"], check=False, timeout=30)
            except (OSError, subprocess.TimeoutExpired) as exc:
                result.warnings.append({"code": "auto_shutdown_failed", "detail": str(exc)})
        else:
            _diag_print(config, "Auto-Shutdown blockiert: Evidence noch nicht dauerhaft gespeichert.")
            result.warnings.append({"code": "auto_shutdown_blocked", "detail": decision.reason})


def run_tui_input_diagnostic(
    config: DiagnosticConfig,
    *,
    persist_resolver: Any = None,
) -> DiagnosticResult:
    result = DiagnosticResult(run_id=config.run_id)
    result.write_actions_blocked = diagnostic_mode_enabled()
    if not result.write_actions_blocked:
        result.warnings.append({"code": "diag_flag_absent", "detail": "running without cmdline flag"})

    evidence_parent = resolve_evidence_root(config)
    run_dir = evidence_parent / config.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    result.runtime_path = str(run_dir)
    assert_path_under_allowed_roots(
        run_dir,
        [Path("/run/setuphelfer"), Path("/media"), Path("/run/media"), Path("/tmp"), evidence_parent],
    )

    try:
        atomic_write_json(
            run_dir / "00-run-meta.json",
            {
                "test_id": "PI-RS-TUI-AUTO-001",
                "run_id": config.run_id,
                "tty_menu": config.tty_menu,
                "tty_diagnostic": config.tty_diagnostic,
                "write_actions_blocked": result.write_actions_blocked,
                "blocked_actions": sorted(blocked_tui_actions()),
                "auto_shutdown": config.auto_shutdown,
                "evidence_strategy": "runtime_first_then_setup_logs",
            },
        )

        identity = _machine_identity_redacted()
        result.machine_identity = identity
        atomic_write_json(run_dir / "01-machine-identity-redacted.json", identity)

        try:
            cmdline = Path("/proc/cmdline").read_text(encoding="utf-8", errors="replace")
        except OSError:
            cmdline = ""
        atomic_write_text(run_dir / "02-kernel-cmdline.txt", cmdline)

        devices = inventory_from_proc_devices()
        result.input_devices = devices
        atomic_write_json(run_dir / "03-input-device-inventory.json", {"devices": devices})

        whip_res = resolve_whiptail_pids()
        selected = whip_res.get("selected") or {}
        pid = str(selected.get("pid") or "")
        fd_info = {"fd0": "", "fd1": "", "fd2": "", "status": "unreadable"}
        cpu_info: dict[str, Any] = {}
        if pid:
            fd_info = analyze_fds(read_proc_fd(pid, 0), read_proc_fd(pid, 1), read_proc_fd(pid, 2))
            sample_n = 3 if config.observe_only else 15
            cpu_info = sample_cpu(pid, samples=sample_n, interval_s=0.2 if config.observe_only else 1.0)

        result.whiptail_analysis = {
            **whip_res,
            **fd_info,
            **cpu_info,
            "pid": pid or None,
            "fd_status": fd_info.get("status"),
        }
        atomic_write_json(run_dir / "07-whiptail-process.json", result.whiptail_analysis)
        atomic_write_text(
            run_dir / "08-whiptail-cpu-samples.jsonl",
            "\n".join(json.dumps(s) for s in (cpu_info.get("samples") or [])) + "\n",
        )
        atomic_write_json(run_dir / "09-whiptail-fds.json", fd_info)

        tty_state = read_tty1_state(config.tty_menu)
        result.tty_analysis = tty_state
        atomic_write_json(run_dir / "10-tty1-state.json", tty_state)

        owners = collect_tty1_owners()
        result.process_analysis = owners
        atomic_write_json(run_dir / "11-tty1-owners.json", owners)

        dump_path = run_dir / "screen_before.txt"
        screen = try_screen_dump(1, dump_path)
        result.screen_analysis = screen
        atomic_write_json(run_dir / "15-screen-comparison.json", screen)

        if config.observe_only or not config.interactive:
            result.internal_keyboard_test = {
                "stage": "internal_keyboard_tty2",
                "status": "skipped",
                "expected_keys": [],
                "tty_keys_received": [],
                "evdev_keys_received": [],
            }
            result.external_keyboard_test = {"stage": "external_keyboard", "status": "skipped"}
            result.menu_input_test = {
                "stage": "tui_menu_tty1",
                "status": "skipped",
                "write_actions_blocked": result.write_actions_blocked,
                "enter_test_skipped_safety_guard_unconfirmed": not result.write_actions_blocked,
            }
        else:
            result.internal_keyboard_test = _run_internal_keyboard_stage(config, devices)
            result.external_keyboard_test = {"stage": "external_keyboard", "status": "skipped_optional"}
            menu_test: dict[str, Any] = {
                "stage": "tui_menu_tty1",
                "write_actions_blocked": result.write_actions_blocked,
            }
            if config.auto_vt_switch and result.write_actions_blocked:
                _diag_print(config, "Wechsel in 5s auf tty1 — bitte Pfeil runter/hoch, Tab, Esc tippen (kein Backup).")
                time.sleep(5)
                menu_test["chvt_to_1"] = chvt_safe(1)
                nodes = [d["event_node"] for d in devices if d.get("event_node")]
                class_map = {
                    d["event_node"]: ("internal" if d.get("is_internal_candidate") else "external")
                    for d in devices
                }
                events: list[dict[str, Any]] = []
                with PassiveEvdevMonitor(nodes, class_by_node=class_map) as mon:
                    deadline = time.monotonic() + float(config.menu_test_timeout_s)
                    while time.monotonic() < deadline:
                        for ev in mon.poll(0.2):
                            if ev.value == 1:
                                events.append(event_to_dict(ev))
                menu_test["evdev_keys_received"] = [e["name"] for e in events]
                menu_test["chvt_to_2"] = chvt_safe(2)
                menu_test["status"] = "completed"
                menu_test["enter_test_skipped_safety_guard_unconfirmed"] = False
                menu_test["enter_test"] = "skipped_by_policy"
            else:
                menu_test["status"] = "enter_test_skipped_safety_guard_unconfirmed"
                menu_test["enter_test_skipped_safety_guard_unconfirmed"] = True
            result.menu_input_test = menu_test
        atomic_write_json(run_dir / "04-internal-keyboard-test.json", result.internal_keyboard_test)
        atomic_write_json(run_dir / "05-external-keyboard-test.json", result.external_keyboard_test)
        atomic_write_json(run_dir / "06-tui-menu-input-test.json", result.menu_input_test)
        atomic_write_json(run_dir / "12-input-events-redacted.jsonl", [])
        atomic_write_text(run_dir / "13-kernel-input-log-redacted.txt", _kernel_input_snippet())
        atomic_write_text(run_dir / "14-systemd-console-status.txt", _systemd_console_status())
        atomic_write_json(run_dir / "16-operator-observations.json", {})

        for candidate in (
            Path("/opt/setuphelfer-rescue/VERSION"),
            Path("/opt/setuphelfer-rescue/config/rescue_payload_version.json"),
        ):
            if candidate.is_file():
                try:
                    if candidate.suffix == ".json":
                        result.payload_version = json.loads(candidate.read_text()).get("rescue_payload_version")
                    else:
                        result.payload_version = candidate.read_text().strip()
                except (OSError, json.JSONDecodeError):
                    pass
                if result.payload_version:
                    break

        result.hypotheses = {
            "fd_status": fd_info.get("status"),
            "cpu_avg_percent": cpu_info.get("cpu_avg_percent"),
            "tty_competition": owners.get("competition"),
            "menu_visible_unusable": True,
            "legacy_high_cpu": float(cpu_info.get("cpu_avg_percent") or 0) >= 20.0,
        }

        decision = evaluate_tui_input_diagnostic(result)
        result.leading_hypothesis = decision.leading_hypothesis
        result.confidence = decision.confidence
        result.recommended_repair_path = decision.recommended_repair_path
        atomic_write_json(
            run_dir / "17-hypothesis-decision.json",
            {
                "leading_hypothesis": decision.leading_hypothesis,
                "confidence": decision.confidence,
                "recommended_repair_path": decision.recommended_repair_path,
                "reasons": decision.reasons,
                "contradicting_evidence": decision.contradicting_evidence,
                "missing_evidence": decision.missing_evidence,
            },
        )

        report = _render_report(result, decision)
        atomic_write_text(run_dir / "19-final-report.md", report)

        if config.observe_only:
            result.status = "review_required"
        elif result.errors:
            result.status = "blocked"
        else:
            result.status = "review_required"

        final = {
            "test_id": "PI-RS-TUI-AUTO-001",
            "run_id": result.run_id,
            "status": result.status,
            "payload_version": result.payload_version,
            "leading_hypothesis": result.leading_hypothesis,
            "confidence": result.confidence,
            "recommended_repair_path": result.recommended_repair_path,
            "write_actions_blocked": result.write_actions_blocked,
            "write_guard": write_guard_response() if result.write_actions_blocked else None,
            "runtime_path": str(run_dir),
        }
        finalize_run_dir(run_dir, status=result.status, final_result=final)
    except Exception as exc:
        result.errors.append({"code": "diagnostic_exception", "detail": str(exc)})
        result.status = "blocked"
        try:
            finalize_run_dir(
                run_dir,
                status="blocked",
                final_result={
                    "test_id": "PI-RS-TUI-AUTO-001",
                    "run_id": result.run_id,
                    "status": "blocked",
                    "error": str(exc),
                    "runtime_path": str(run_dir),
                },
            )
        except Exception as finalize_exc:
            result.errors.append({"code": "finalize_failed", "detail": str(finalize_exc)})
    finally:
        try:
            _apply_persistence(config, result, run_dir, resolver=persist_resolver)
        except Exception as persist_exc:
            result.errors.append({"code": "persistence_failed", "detail": str(persist_exc)})
            result.shutdown_allowed = False
            result.persistence_status = "blocked"
    return result



def _diag_print(config: DiagnosticConfig, msg: str) -> None:
    tty = config.tty_diagnostic
    try:
        with open(tty, "w", encoding="utf-8", errors="replace") as fh:
            fh.write(msg + "\n")
            fh.flush()
    except OSError:
        print(msg, flush=True)


def _run_internal_keyboard_stage(config: DiagnosticConfig, devices: list[dict[str, Any]]) -> dict[str, Any]:
    expected = ["KEY_UP", "KEY_DOWN", "KEY_TAB", "KEY_ESC", "KEY_ENTER", "KEY_A"]
    _diag_print(
        config,
        "Interner Tastaturtest: bitte nacheinander Pfeil hoch/runter, Tab, Esc, Enter, A tippen.",
    )
    nodes = [d["event_node"] for d in devices if d.get("is_internal_candidate") and d.get("event_node")]
    if not nodes:
        nodes = [d["event_node"] for d in devices if d.get("event_node")]
    class_map = {
        d["event_node"]: ("internal" if d.get("is_internal_candidate") else "external") for d in devices
    }
    received: list[str] = []
    with PassiveEvdevMonitor(nodes, class_by_node=class_map) as mon:
        for name in expected:
            _diag_print(config, f"Erwarte: {name} (Timeout {config.input_test_timeout_s}s)")
            got = mon.collect_until(wanted_names={name}, timeout_s=float(config.input_test_timeout_s))
            if any(ev.name == name for ev in got):
                received.append(name)
    status = "passed" if len(received) == len(expected) else ("partial" if received else "timeout")
    return {
        "stage": "internal_keyboard_tty2",
        "expected_keys": expected,
        "tty_keys_received": [],
        "evdev_keys_received": received,
        "device": nodes[0] if nodes else "",
        "status": status,
    }


def _machine_identity_redacted() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, path in (
        ("product_name", "/sys/class/dmi/id/product_name"),
        ("board_name", "/sys/class/dmi/id/board_name"),
        ("bios_version", "/sys/class/dmi/id/bios_version"),
        ("sys_vendor", "/sys/class/dmi/id/sys_vendor"),
    ):
        try:
            out[key] = Path(path).read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            out[key] = ""
    return out


def _kernel_input_snippet() -> str:
    try:
        proc = subprocess.run(
            ["dmesg"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        lines = [
            ln
            for ln in (proc.stdout or "").splitlines()
            if re.search(r"keyboard|input|hid|i8042|atkbd|serio|tty|newt|whiptail", ln, re.I)
        ]
        return "\n".join(lines[-300:]) + ("\n" if lines else "")
    except (OSError, subprocess.TimeoutExpired):
        return ""


def _systemd_console_status() -> str:
    units = [
        "setuphelfer-rescue-tui.service",
        "setuphelfer-rescue-tui-input-diagnostic.service",
        "getty@tty1.service",
        "getty@tty2.service",
        "setuphelfer-rescue-boot-progress.service",
        "setuphelfer-rescue-start-assistant.service",
    ]
    chunks: list[str] = []
    for u in units:
        try:
            proc = subprocess.run(
                ["systemctl", "status", u, "--no-pager", "-l"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            chunks.append(f"===== {u} =====\n{(proc.stdout or proc.stderr or 'not_present')[:2000]}\n")
        except (OSError, subprocess.TimeoutExpired):
            chunks.append(f"===== {u} =====\nnot_present\n")
    return "\n".join(chunks)


def _render_report(result: DiagnosticResult, decision: Any) -> str:
    return "\n".join(
        [
            "# Setuphelfer TUI-Eingabediagnose",
            "",
            f"Run-ID: {result.run_id}",
            f"Status: {result.status}",
            f"Payload: {result.payload_version}",
            f"Leading hypothesis: {result.leading_hypothesis}",
            f"Confidence: {result.confidence}",
            f"Recommended repair path: {result.recommended_repair_path}",
            f"Write actions blocked: {result.write_actions_blocked}",
            "",
            "## Reasons",
            *[f"- {r}" for r in (decision.reasons or ["—"])],
            "",
            "## Missing evidence",
            *[f"- {m}" for m in (decision.missing_evidence or ["—"])],
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    import argparse
    import signal

    parser = argparse.ArgumentParser(description="Setuphelfer TUI input diagnostic (read-only)")
    parser.add_argument("--observe-only", action="store_true", help="No interactive prompts / VT switches")
    parser.add_argument("--evidence-root", type=Path, default=None)
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args(argv)

    if not diagnostic_mode_enabled() and not args.observe_only:
        # Refuse accidental start outside diagnose entry unless observe-only/testing
        print("setuphelfer_tui_input_diag=1 required (or pass --observe-only)", flush=True)
        return 2

    cfg = config_from_cmdline(evidence_root=args.evidence_root, interactive=not args.observe_only)
    cfg = replace(
        cfg,
        observe_only=bool(args.observe_only),
        interactive=not bool(args.observe_only),
        run_id=args.run_id or cfg.run_id or default_run_id(),
        evidence_root=args.evidence_root or cfg.evidence_root,
    )

    def _on_term(signum: int, _frame: Any) -> None:
        # Raise so run_tui_input_diagnostic's finally still runs persistence.
        raise SystemExit(128 + int(signum))

    try:
        signal.signal(signal.SIGTERM, _on_term)
    except (OSError, ValueError):
        pass

    result = run_tui_input_diagnostic(cfg)
    print(
        json.dumps(
            {
                "status": result.status,
                "run_id": result.run_id,
                "hypothesis": result.leading_hypothesis,
                "persistence_status": result.persistence_status,
                "persistent_path": result.persistent_path,
                "shutdown_allowed": result.shutdown_allowed,
                "runtime_path": result.runtime_path,
            },
            ensure_ascii=False,
        )
    )
    if not result.shutdown_allowed and result.persistence_status != "persisted":
        return 3
    return 0 if result.status in {"passed", "review_required"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
