"""Hypothesis / repair-path evaluation for TUI input diagnostic."""

from __future__ import annotations

from typing import Any

from core.rescue_tui_input_diagnostic_contract import DiagnosticDecision, DiagnosticResult


def evaluate_tui_input_diagnostic(result: DiagnosticResult) -> DiagnosticDecision:
    missing: list[str] = []
    reasons: list[str] = []
    contradict: list[str] = []

    whip = result.whiptail_analysis or {}
    tty = result.tty_analysis or {}
    menu = result.menu_input_test or {}
    internal = result.internal_keyboard_test or {}
    external = result.external_keyboard_test or {}
    proc = result.process_analysis or {}
    screen = result.screen_analysis or {}
    hyp_in = result.hypotheses or {}

    fd_status = str(whip.get("fd_status") or hyp_in.get("fd_status") or "")
    fd0 = str(whip.get("fd0") or "")
    fd1 = str(whip.get("fd1") or "")
    avg_cpu = float(whip.get("cpu_avg_percent") or hyp_in.get("cpu_avg_percent") or 0.0)
    cpu_class = str(whip.get("cpu_class") or "")
    competing = bool((proc.get("competing_writer_detected") if proc else False) or hyp_in.get("competing_writer"))
    competition_sev = str(proc.get("severity") or hyp_in.get("tty_competition") or "none")

    evdev_ok = bool(internal.get("evdev_keys_received") or menu.get("evdev_keys_received"))
    tty2_ok = str(internal.get("status") or "") in {"passed", "partial"}
    tty2_failed = str(internal.get("status") or "") in {"failed", "timeout"}
    external_ok = str(external.get("status") or "") in {"passed", "partial"}
    internal_failed = tty2_failed and not evdev_ok
    raw_mode = bool(tty.get("raw_mode_detected"))
    suspicious_flags = list(tty.get("suspicious_flags") or [])
    screen_unchanged = bool(screen.get("all_dumps_identical"))
    menu_keys_seen = bool(menu.get("evdev_keys_received"))
    operator = menu.get("operator_observations") or {}

    # FD mismatch — confirmed
    if fd_status == "mismatch" or _fd_is_bad(fd0) or (fd0 and fd1 and fd0 != fd1 and "/dev/tty" in fd1):
        reasons.append("stdin/stdout FD mismatch on TUI/whiptail process")
        return DiagnosticDecision(
            leading_hypothesis="fd_mismatch",
            confidence="confirmed",
            recommended_repair_path="D_tui_service_fd_or_tty_ownership",
            reasons=reasons,
            contradicting_evidence=contradict,
            missing_evidence=missing,
        )

    # H6
    if internal_failed and (not external_ok) and hyp_in.get("kernel_input_errors"):
        reasons.append("no internal/external key events and kernel input errors")
        return DiagnosticDecision(
            leading_hypothesis="H6_input_driver",
            confidence="high",
            recommended_repair_path="A_kernel_input_fix",
            reasons=reasons,
            contradicting_evidence=contradict,
            missing_evidence=missing,
        )
    if internal_failed and external_ok:
        reasons.append("external USB keyboard works; internal does not")
        return DiagnosticDecision(
            leading_hypothesis="H6_input_driver",
            confidence="high",
            recommended_repair_path="A_kernel_input_fix",
            reasons=reasons,
            contradicting_evidence=contradict,
            missing_evidence=missing,
        )

    # TTY competition
    if competing or competition_sev in {"strong", "confirmed"}:
        reasons.append("competing writers on tty1")
        return DiagnosticDecision(
            leading_hypothesis="tty_competition",
            confidence="high" if competition_sev != "confirmed" else "confirmed",
            recommended_repair_path="D_tui_service_fd_or_tty_ownership",
            reasons=reasons,
            contradicting_evidence=contradict,
            missing_evidence=missing,
        )

    # H4
    if (tty2_ok or evdev_ok) and fd_status in {"ok", ""} and (raw_mode or suspicious_flags):
        reasons.append("input works; tty1 terminal flags suspicious")
        return DiagnosticDecision(
            leading_hypothesis="H4_terminal_state",
            confidence="high",
            recommended_repair_path="B_terminal_init_and_tty_reset",
            reasons=reasons,
            contradicting_evidence=contradict,
            missing_evidence=missing,
        )

    # H7
    high_cpu = avg_cpu >= 20.0 or cpu_class == "high_poll_or_redraw"
    if (menu_keys_seen or evdev_ok) and fd_status in {"ok", ""} and high_cpu and not competing:
        if operator.get("menu_unchanged") is True or screen_unchanged:
            reasons.append("keys reach kernel; FDs ok; high CPU; screen/menu unchanged")
            return DiagnosticDecision(
                leading_hypothesis="H7_newt_redraw",
                confidence="high",
                recommended_repair_path="C_whiptail_newt_harden_or_replace",
                reasons=reasons,
                contradicting_evidence=contradict,
                missing_evidence=missing,
            )
        reasons.append("keys seen; FDs ok; elevated whiptail CPU")
        return DiagnosticDecision(
            leading_hypothesis="H7_newt_redraw",
            confidence="high",
            recommended_repair_path="C_whiptail_newt_harden_or_replace",
            reasons=reasons,
            contradicting_evidence=contradict,
            missing_evidence=missing,
        )

    # Historical MSI symptom without full interactive run
    if hyp_in.get("legacy_high_cpu") and hyp_in.get("menu_visible_unusable"):
        reasons.append("prior evidence: visible menu + high whiptail CPU")
        missing.extend(["vt_switch_result", "live_fd_snapshot", "operator_menu_observations"])
        return DiagnosticDecision(
            leading_hypothesis="H7_newt_redraw",
            confidence="medium",
            recommended_repair_path="C_whiptail_newt_harden_or_replace",
            reasons=reasons,
            contradicting_evidence=contradict,
            missing_evidence=missing,
        )

    if not whip.get("pid"):
        missing.append("whiptail_pid")
    if not internal:
        missing.append("internal_keyboard_test")
    if not menu:
        missing.append("menu_input_test")

    return DiagnosticDecision(
        leading_hypothesis="undetermined",
        confidence="medium" if missing else "low",
        recommended_repair_path="additional_targeted_diagnostic",
        reasons=reasons or ["insufficient evidence for high-confidence hypothesis"],
        contradicting_evidence=contradict,
        missing_evidence=missing,
    )


def _fd_is_bad(fd0: str) -> bool:
    if not fd0:
        return False
    if fd0 == "/dev/null" or fd0.startswith("pipe:") or fd0.startswith("socket:"):
        return True
    if fd0.startswith("/dev/tty") and fd0 not in {"/dev/tty1", "/dev/tty"}:
        # tty2 while menu on tty1
        return fd0 != "/dev/tty1"
    return False


def classify_cpu(avg_percent: float) -> str:
    if avg_percent < 5.0:
        return "idle_expected"
    if avg_percent < 20.0:
        return "suspicious"
    return "high_poll_or_redraw"


def analyze_fds(fd0: str | None, fd1: str | None, fd2: str | None, *, expected_tty: str = "/dev/tty1") -> dict[str, Any]:
    f0 = fd0 or ""
    f1 = fd1 or ""
    f2 = fd2 or ""
    if not f0 and not f1 and not f2:
        return {"fd0": f0, "fd1": f1, "fd2": f2, "fd_consistent": False, "status": "unreadable"}
    bad = _fd_is_bad(f0) or (f0 and f1 and f0 != f1)
    ok = (not bad) and (not f0 or f0 == expected_tty or f0 == "/dev/tty")
    return {
        "fd0": f0,
        "fd1": f1,
        "fd2": f2,
        "fd_consistent": (f0 == f1 == f2) if (f0 and f1 and f2) else False,
        "status": "mismatch" if bad else ("ok" if ok else "mismatch"),
    }
