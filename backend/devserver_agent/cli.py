"""CLI für den Setuphelfer Development Agent."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from devserver_agent.client import health_check, post_report, validate_server_health
from devserver_agent.collector import build_dev_node_from_config, build_dev_report_from_collection
from devserver_agent.config import load_dev_agent_config, validate_server_url
from devserver_agent.models import resolve_node_identity
from devserver_agent.redaction_client import enforce_mode_redaction
from devserver_agent.rescue_profile import (
    default_developer_profile_root,
    default_public_profile_root,
    validate_developer_profile,
    validate_public_profile_guard,
)
from devserver_agent.spool import AgentSpool

EXIT_OK = 0
EXIT_DISABLED = 10
EXIT_PUBLIC_BLOCKED = 11
EXIT_SPOOLED = 12
EXIT_REDACTION_FAILED = 13
EXIT_UPLOAD_FAILED = 14
EXIT_UNKNOWN = 20


def _emit(result: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result.get("code", result.get("status", "ok")))


def _apply_cli_overrides(args: argparse.Namespace) -> None:
    if args.mode:
        os.environ["SETUPHELFER_DEV_AGENT_MODE"] = args.mode
    if args.server:
        os.environ["SETUPHELFER_DEV_AGENT_SERVER_URL"] = args.server
    if args.node_id:
        os.environ["SETUPHELFER_DEV_AGENT_NODE_ID"] = args.node_id
    if args.display_name:
        os.environ["SETUPHELFER_DEV_AGENT_DISPLAY_NAME"] = args.display_name
    if getattr(args, "send", False) or getattr(args, "collect_only", False):
        if args.mode == "local_lab" or os.environ.get("SETUPHELFER_DEV_AGENT_MODE") == "local_lab":
            os.environ.setdefault("SETUPHELFER_DEV_AGENT_ENABLED", "true")
            os.environ.setdefault("SETUPHELFER_DEV_AGENT_AUTO_UPLOAD", "true")


def cmd_health(args: argparse.Namespace) -> int:
    cfg = load_dev_agent_config()
    url_ok, url_err = validate_server_url(cfg.server_url)
    if not url_ok:
        _emit({"code": "DEV_AGENT_URL_BLOCKED", "error": url_err}, as_json=args.json)
        return EXIT_UPLOAD_FAILED
    result = health_check(cfg.server_url, timeout=cfg.timeout_seconds)
    validated = validate_server_health(result, cfg.mode)
    out = {"code": "DEV_AGENT_HEALTH_OK" if validated["ok"] else "DEV_AGENT_HEALTH_FAILED", **result, **validated}
    _emit(out, as_json=args.json)
    return EXIT_OK if validated["ok"] else EXIT_UPLOAD_FAILED


def cmd_collect(args: argparse.Namespace) -> int:
    _apply_cli_overrides(args)
    cfg = load_dev_agent_config()
    node_id, display_name = resolve_node_identity(cfg.node_id, cfg.display_name)
    node = build_dev_node_from_config(node_id=node_id, display_name=display_name, mode=cfg.mode)
    report, _payload = build_dev_report_from_collection(
        node_id=node_id,
        mode=cfg.mode,
        collect_hardware=cfg.collect_hardware,
        collect_storage=cfg.collect_storage,
        collect_boot=cfg.collect_boot,
    )
    out = {"code": "DEV_AGENT_COLLECT_OK", "node": node, "report": report}
    _emit(out, as_json=args.json)
    return EXIT_OK


def cmd_send(args: argparse.Namespace) -> int:
    _apply_cli_overrides(args)
    cfg = load_dev_agent_config()

    if not cfg.enabled:
        _emit({"code": "DEV_AGENT_DISABLED", "errors": ["agent_disabled"]}, as_json=args.json)
        return EXIT_DISABLED

    if cfg.mode == "public_rescue":
        _emit({"code": "DEV_AGENT_PUBLIC_UPLOAD_BLOCKED", "errors": ["public_rescue_no_auto_upload"]}, as_json=args.json)
        return EXIT_PUBLIC_BLOCKED

    if not cfg.upload_allowed:
        _emit({"code": "DEV_AGENT_UPLOAD_NOT_ALLOWED", "errors": ["auto_upload_disabled"]}, as_json=args.json)
        return EXIT_DISABLED

    url_ok, url_err = validate_server_url(cfg.server_url)
    if not url_ok:
        _emit({"code": "DEV_AGENT_URL_BLOCKED", "error": url_err}, as_json=args.json)
        return EXIT_UPLOAD_FAILED

    node_id, display_name = resolve_node_identity(cfg.node_id, cfg.display_name)
    node = build_dev_node_from_config(node_id=node_id, display_name=display_name, mode=cfg.mode)
    report, _payload = build_dev_report_from_collection(
        node_id=node_id,
        mode=cfg.mode,
        collect_hardware=cfg.collect_hardware,
        collect_storage=cfg.collect_storage,
        collect_boot=cfg.collect_boot,
    )

    report, redact_warnings, redact_errors = enforce_mode_redaction(cfg.mode, report)
    if redact_errors:
        _emit({"code": "DEV_AGENT_REDACTION_FAILED", "errors": redact_errors}, as_json=args.json)
        return EXIT_REDACTION_FAILED

    report.setdefault("warnings", []).extend(redact_warnings)

    hc = health_check(cfg.server_url, timeout=cfg.timeout_seconds)
    validated = validate_server_health(hc, cfg.mode)
    if not validated["ok"]:
        spool = AgentSpool(cfg.spool_dir)
        spooled = spool.save_spooled_report(node, report, reason=",".join(validated["errors"]))
        _emit({
            "code": "DEV_AGENT_SPOOLED",
            "reason": validated["errors"],
            "spool": spooled,
        }, as_json=args.json)
        return EXIT_SPOOLED

    upload = post_report(cfg.server_url, node, report, cfg.token, timeout=cfg.timeout_seconds)
    if not upload.get("ok"):
        err = str(upload.get("error") or "")
        if upload.get("http_status") == 0 or "timed out" in err.lower() or "refused" in err.lower():
            spool = AgentSpool(cfg.spool_dir)
            spooled = spool.save_spooled_report(node, report, reason=err or "server_unreachable")
            _emit({"code": "DEV_AGENT_SPOOLED", "upload": upload, "spool": spooled}, as_json=args.json)
            return EXIT_SPOOLED
        _emit({"code": "DEV_AGENT_UPLOAD_FAILED", "upload": upload}, as_json=args.json)
        return EXIT_UPLOAD_FAILED

    resp = upload.get("response") or {}
    _emit({
        "code": "DEV_AGENT_UPLOAD_OK",
        "node_id": resp.get("node_id"),
        "report_id": resp.get("report_id"),
        "redaction_status": resp.get("redaction_status"),
        "upload": upload,
    }, as_json=args.json)
    return EXIT_OK


EXIT_PROFILE_INVALID = 15


def cmd_validate_rescue_profile(args: argparse.Namespace) -> int:
    dev_root = Path(args.profile_root) if args.profile_root else default_developer_profile_root()
    pub_root = default_public_profile_root()
    dev = validate_developer_profile(dev_root)
    pub = validate_public_profile_guard(pub_root)
    out = {
        "code": "DEV_AGENT_RESCUE_PROFILE_OK" if dev["ok"] and pub["ok"] else "DEV_AGENT_RESCUE_PROFILE_FAILED",
        "developer": dev,
        "public_guard": pub,
    }
    _emit(out, as_json=args.json)
    return EXIT_OK if dev["ok"] and pub["ok"] else EXIT_PROFILE_INVALID


def cmd_spool_list(args: argparse.Namespace) -> int:
    cfg = load_dev_agent_config()
    spool = AgentSpool(cfg.spool_dir)
    out = spool.list_spooled_reports()
    _emit({"code": "DEV_AGENT_SPOOL_LIST", **out}, as_json=args.json)
    return EXIT_OK


def cmd_spool_retry(args: argparse.Namespace) -> int:
    cfg = load_dev_agent_config()
    if not cfg.enabled or cfg.mode == "public_rescue":
        _emit({"code": "DEV_AGENT_RETRY_BLOCKED"}, as_json=args.json)
        return EXIT_DISABLED
    spool = AgentSpool(cfg.spool_dir)

    def _upload(node: dict, report: dict) -> dict:
        report, _, errors = enforce_mode_redaction(cfg.mode, report)
        if errors:
            return {"ok": False, "code": "redaction_failed"}
        return post_report(cfg.server_url, node, report, cfg.token, timeout=cfg.timeout_seconds)

    out = spool.retry_spooled_reports(upload_fn=_upload)
    _emit({"code": "DEV_AGENT_SPOOL_RETRY", **out}, as_json=args.json)
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Setuphelfer Development Agent")
    p.add_argument("--collect-only", action="store_true")
    p.add_argument("--send", action="store_true")
    p.add_argument("--health", action="store_true")
    p.add_argument("--mode", choices=["public_rescue", "beta_opt_in", "local_lab"])
    p.add_argument("--server")
    p.add_argument("--node-id")
    p.add_argument("--display-name")
    p.add_argument("--spool-list", action="store_true")
    p.add_argument("--spool-retry", action="store_true")
    p.add_argument("--validate-rescue-profile", action="store_true")
    p.add_argument("--profile-root")
    p.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.health:
            return cmd_health(args)
        if args.spool_list:
            return cmd_spool_list(args)
        if args.spool_retry:
            return cmd_spool_retry(args)
        if args.validate_rescue_profile:
            return cmd_validate_rescue_profile(args)
        if args.collect_only:
            return cmd_collect(args)
        if args.send:
            return cmd_send(args)
        return cmd_collect(args)
    except Exception as exc:
        _emit({"code": "DEV_AGENT_UNKNOWN_ERROR", "error": str(exc)}, as_json=args.json)
        return EXIT_UNKNOWN


if __name__ == "__main__":
    sys.exit(main())
