"""
Read-only scan of repo evidence for Development Control Center report/test feeds.

No shell, no writes, no full large-file payloads.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

UTC = timezone.utc

_DEFAULT_LIMIT = 5
_MAX_SCAN_FILES = 800
_MAX_READ_BYTES = 8192
_MAX_SUMMARY_CHARS = 280

# Whitelisted roots relative to repo (no build/, no secrets).
_EVIDENCE_ROOTS: tuple[str, ...] = (
    "docs/evidence/rescue",
    "docs/evidence/dev-dashboard",
    "docs/evidence/diagnostics",
    "docs/evidence/runtime-results/rescue",
    "docs/evidence/runtime-results/dev-dashboard",
    "docs/evidence/lab-acceptance",
)

_SKIP_SUFFIXES = frozenset(
    {
        ".log",
        ".png",
        ".jpg",
        ".sha256",
        ".qcow2",
        ".img",
        ".raw",
        ".deb",
        ".pyc",
    }
)

_REPORT_MD_MARKERS = (
    "_RESULT.md",
    "_REVIEW.md",
    "_INGEST_",
    "_PHASE0.md",
    "_CLASSIFICATION.md",
    "_AUDIT.md",
    "_DECISION.md",
)

_REPORT_JSON_NAMES = (
    "latest.json",
    "_latest.json",
    "summary.json",
    "_summary.json",
)

_DATE_LINE_RE = re.compile(
    r"(?:\*\*Datum:\*\*|Datum:|\"generated_at\"|\"created_at\"|\"started_at\"|\"completed_at\"|\"ended_at\")\s*"
    r"([0-9]{4}-[0-9]{2}-[0-9]{2}(?:[T ][0-9:\-+Z]+)?)",
    re.I,
)

_STATUS_FROM_NAME_RE = re.compile(
    r"(ok|blocked|review_required|ready_for|failed|partial|success|timeout)",
    re.I,
)

_CATEGORY_RULES: tuple[tuple[str, str], ...] = (
    ("qemu", "qemu"),
    ("fleet", "fleet"),
    ("rescue_agent", "rescue_agent"),
    ("rescue-agent", "rescue_agent"),
    ("developer_qemu", "rescue"),
    ("controlled_iso", "rescue"),
    ("dev-dashboard", "dev_dashboard"),
    ("diagnostics", "diagnostics"),
    ("backup", "backup"),
    ("restore", "restore"),
    ("runtime-results", "runtime"),
    ("lab-acceptance", "diagnostics"),
    ("manual_command", "dev_dashboard"),
)

_VALID_CATEGORIES = frozenset(
    {"rescue", "qemu", "fleet", "rescue_agent", "dev_dashboard", "diagnostics", "backup", "restore", "runtime", "other"},
)
_VALID_STATUSES = frozenset(
    {"ok", "green", "review_required", "blocked", "failed", "partial_green", "yellow", "unknown"},
)
_VALID_TIME_RANGES = frozenset({"today", "24h", "7d", "all"})


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _iso_now() -> str:
    return datetime.now(tz=UTC).isoformat()


def _parse_timestamp(raw: str | None) -> datetime | None:
    if not raw or not str(raw).strip():
        return None
    s = str(raw).strip()[:32]
    try:
        if s.endswith("Z"):
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        return datetime.fromisoformat(s)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s[:19], fmt)
            return dt.replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


def _mtime_dt(path: Path) -> datetime | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    except OSError:
        return None


def _infer_category(rel: str) -> str:
    low = rel.lower().replace("\\", "/")
    for needle, cat in _CATEGORY_RULES:
        if needle in low:
            return cat
    return "other"


def _infer_status_from_name(name: str) -> str:
    low = name.lower()
    if "blocked" in low:
        return "blocked"
    if "review_required" in low or "review-required" in low:
        return "review_required"
    if "ready_for" in low or "_ok" in low or low.endswith("_ok.md"):
        return "ok"
    if "failed" in low or "failure" in low:
        return "failed"
    if "partial" in low:
        return "partial_green"
    m = _STATUS_FROM_NAME_RE.search(name)
    if m:
        val = m.group(1).lower()
        if val in ("success", "ready_for"):
            return "ok"
        if val == "timeout":
            return "failed"
        return val if val in _VALID_STATUSES else "unknown"
    return "unknown"


def _status_from_json(data: dict[str, Any]) -> str:
    for key in ("status", "overall_status", "ampel"):
        raw = data.get(key)
        if raw is None:
            continue
        s = str(raw).lower()
        if s in _VALID_STATUSES:
            return s
        if s in ("success", "ready_for_qemu_guest_agent_smoke_operator_run"):
            return "ok"
        if "blocked" in s:
            return "blocked"
        if "review" in s:
            return "review_required"
        if s in ("red", "rot"):
            return "failed"
        if s in ("gelb", "yellow"):
            return "yellow"
        if s in ("green", "gruen", "grün"):
            return "green"
    return "unknown"


def _extract_timestamp_from_text(text: str, *, mtime: datetime | None) -> datetime | None:
    best: datetime | None = None
    for m in _DATE_LINE_RE.finditer(text[: _MAX_READ_BYTES]):
        dt = _parse_timestamp(m.group(1))
        if dt and (best is None or dt > best):
            best = dt
    if best:
        return best
    return mtime


def _title_from_path(rel: str) -> str:
    name = Path(rel).name
    if name.endswith(".md"):
        return name[:-3].replace("_", " ")
    if name.endswith(".json"):
        return name.replace("_", " ")
    return name


def _should_include_file(path: Path) -> bool:
    name = path.name
    if name.startswith("."):
        return False
    low = name.lower()
    if any(low.endswith(suf) for suf in _SKIP_SUFFIXES):
        return False
    if low.endswith(".md"):
        return any(marker in name for marker in _REPORT_MD_MARKERS) or name.startswith("DCC_")
    if low.endswith(".json"):
        return any(pat in low for pat in _REPORT_JSON_NAMES) or "smoke" in low or "ingest" in low
    return False


def _read_snippet(path: Path) -> tuple[str, dict[str, Any] | None]:
    try:
        if path.stat().st_size > 512_000:
            return "", None
        raw = path.read_text(encoding="utf-8", errors="replace")[:_MAX_READ_BYTES]
    except OSError:
        return "", None
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return raw, data
        except json.JSONDecodeError:
            pass
    return raw, None


def _scan_report_candidates(repo: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    scanned = 0
    for rel_root in _EVIDENCE_ROOTS:
        base = repo / rel_root
        if not base.is_dir():
            continue
        try:
            for fp in base.rglob("*"):
                if scanned >= _MAX_SCAN_FILES:
                    break
                if not fp.is_file() or not _should_include_file(fp):
                    continue
                scanned += 1
                try:
                    rel = str(fp.relative_to(repo)).replace("\\", "/")
                except ValueError:
                    continue
                mtime = _mtime_dt(fp)
                snippet, jdata = _read_snippet(fp)
                ts = _extract_timestamp_from_text(snippet, mtime=mtime)
                status = _status_from_json(jdata) if jdata else _infer_status_from_name(fp.name)
                head = None
                if jdata:
                    head = jdata.get("head") or jdata.get("git_head")
                summary = ""
                if jdata:
                    for key in ("task", "next_recommended_action", "root_cause_classification", "run_id"):
                        if jdata.get(key):
                            summary = f"{key}={jdata.get(key)}"
                            break
                elif snippet:
                    for line in snippet.splitlines()[:12]:
                        if line.strip().startswith("##") or "**" in line:
                            summary = line.strip()[:_MAX_SUMMARY_CHARS]
                            break
                try:
                    size_bytes = int(fp.stat().st_size)
                except OSError:
                    size_bytes = None
                items.append(
                    {
                        "title": _title_from_path(rel),
                        "path": rel,
                        "category": _infer_category(rel),
                        "status": status,
                        "timestamp": ts.isoformat() if ts else (mtime.isoformat() if mtime else None),
                        "timestamp_source": "embedded" if ts and mtime and ts != mtime else ("mtime" if mtime else "unknown"),
                        "source": "repo_evidence",
                        "summary": summary[:_MAX_SUMMARY_CHARS] if summary else None,
                        "head": str(head) if head else None,
                        "size_bytes": size_bytes,
                        "is_latest": False,
                    }
                )
        except OSError:
            continue
    return items


def _sort_key(item: dict[str, Any]) -> str:
    return str(item.get("timestamp") or "")


def _apply_filters(
    items: list[dict[str, Any]],
    *,
    category: str | None,
    status: str | None,
    search: str | None,
    time_range: str | None,
) -> list[dict[str, Any]]:
    out = list(items)
    now = datetime.now(tz=UTC)
    tr = (time_range or "all").strip().lower()
    if tr not in _VALID_TIME_RANGES:
        tr = "all"
    if tr != "all":
        if tr == "today":
            cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif tr == "24h":
            cutoff = now - timedelta(hours=24)
        else:
            cutoff = now - timedelta(days=7)
        filtered: list[dict[str, Any]] = []
        for it in out:
            dt = _parse_timestamp(str(it.get("timestamp") or ""))
            if dt and dt >= cutoff:
                filtered.append(it)
        out = filtered

    cat = (category or "").strip().lower()
    if cat and cat != "all" and cat in _VALID_CATEGORIES:
        out = [it for it in out if str(it.get("category") or "") == cat]

    st = (status or "").strip().lower()
    if st and st != "all" and st in _VALID_STATUSES:
        out = [it for it in out if str(it.get("status") or "unknown") == st]

    q = (search or "").strip().lower()
    if q:
        out = [
            it
            for it in out
            if q in str(it.get("title") or "").lower()
            or q in str(it.get("path") or "").lower()
            or q in str(it.get("summary") or "").lower()
        ]
    return out


def _build_recent_tests(repo: Path, *, limit: int) -> list[dict[str, Any]]:
    tests: list[dict[str, Any]] = []
    try:
        from core.dev_dashboard_manual_command_runs import build_manual_command_runs_index

        runs_payload = build_manual_command_runs_index(repo_root=repo, max_runs=min(40, limit * 4))
        for run in runs_payload.get("runs") or []:
            tests.append(
                {
                    "title": str(run.get("run_id") or "manual_run"),
                    "path": str(run.get("source_file") or ""),
                    "category": "dev_dashboard",
                    "status": str((run.get("summary") or {}).get("status") or "unknown"),
                    "timestamp": run.get("created_at"),
                    "source": "manual_command_run",
                    "summary": str((run.get("summary") or {}).get("reason") or "")[:200] or None,
                    "head": run.get("head"),
                }
            )
    except Exception:
        pass

    gates = repo / "docs/evidence/release-gates/current_failures.json"
    if gates.is_file():
        try:
            data = json.loads(gates.read_text(encoding="utf-8", errors="replace")[:_MAX_READ_BYTES])
            summ = data.get("summary") if isinstance(data, dict) else {}
            mtime = _mtime_dt(gates)
            tests.append(
                {
                    "title": "pytest current_failures gate",
                    "path": str(gates.relative_to(repo)).replace("\\", "/"),
                    "category": "runtime",
                    "status": str(data.get("ampel") or "unknown").lower(),
                    "timestamp": mtime.isoformat() if mtime else None,
                    "source": "release_gate",
                    "summary": f"failed={summ.get('failed')} passed={summ.get('passed')}",
                    "head": None,
                }
            )
        except (OSError, json.JSONDecodeError):
            pass

    tests.sort(key=_sort_key, reverse=True)
    if tests:
        tests[0]["is_latest"] = True
    return tests[:limit]


def build_recent_evidence_feed(
    repo_root: Path | None = None,
    *,
    limit: int | None = None,
    category: str | None = None,
    status: str | None = None,
    search: str | None = None,
    time_range: str | None = None,
) -> dict[str, Any]:
    """Aggregate recent evidence reports and test runs for DCC."""
    repo = repo_root or _repo_root()
    lim = max(1, min(int(limit or _DEFAULT_LIMIT), 50))
    warnings: list[str] = []

    candidates = _scan_report_candidates(repo)
    candidates.sort(key=_sort_key, reverse=True)
    if candidates:
        candidates[0]["is_latest"] = True

    filtered_reports = _apply_filters(
        candidates,
        category=category,
        status=status,
        search=search,
        time_range=time_range,
    )
    total_reports = len(filtered_reports)
    recent_reports = filtered_reports[:lim]

    recent_tests = _build_recent_tests(repo, limit=lim)

    return {
        "status": "success",
        "read_only": True,
        "generated_at": _iso_now(),
        "default_limit": _DEFAULT_LIMIT,
        "limit": lim,
        "total_count": total_reports,
        "total_reports_unfiltered": len(candidates),
        "items": recent_reports,
        "recent_reports": recent_reports,
        "recent_tests": recent_tests,
        "report_filters": {
            "categories": sorted(_VALID_CATEGORIES),
            "statuses": sorted(_VALID_STATUSES),
            "time_ranges": sorted(_VALID_TIME_RANGES),
            "default_limit": _DEFAULT_LIMIT,
        },
        "warnings": warnings,
    }


def build_recent_evidence_for_summary(repo_root: Path | None = None) -> dict[str, Any]:
    """Default feed for control-center-summary (5 newest, no filter)."""
    return build_recent_evidence_feed(repo_root=repo_root, limit=_DEFAULT_LIMIT)
