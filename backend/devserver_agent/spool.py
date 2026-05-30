"""Offline-Spool für fehlgeschlagene Agent-Uploads."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UTC = timezone.utc
MAX_SPOOL_FILE_BYTES = 512 * 1024


class AgentSpoolError(Exception):
    pass


def _validate_id(value: str) -> str:
    s = (value or "").strip()
    if not s or len(s) > 128:
        raise AgentSpoolError("invalid_id")
    for bad in ("..", "/", "\\"):
        if bad in s:
            raise AgentSpoolError("invalid_id")
    return s


def _ensure_under_root(path: Path, root: Path) -> Path:
    root_res = root.resolve()
    if path.is_symlink():
        raise AgentSpoolError("symlink_blocked")
    resolved = path.resolve()
    root_s = str(root_res)
    resolved_s = str(resolved)
    if resolved_s != root_s and not resolved_s.startswith(root_s + os.sep):
        raise AgentSpoolError("path_traversal")
    return resolved


def _atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise AgentSpoolError("symlink_blocked")
    content = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)
    if len(content.encode("utf-8")) > MAX_SPOOL_FILE_BYTES:
        raise AgentSpoolError("spool_file_too_large")
    tmp = path.with_suffix(".tmp")
    tmp.write_text(content + "\n", encoding="utf-8")
    os.replace(tmp, path)


class AgentSpool:
    def __init__(self, spool_dir: Path) -> None:
        self.root = spool_dir.resolve()

    def save_spooled_report(
        self,
        node: dict[str, Any],
        report: dict[str, Any],
        reason: str,
    ) -> dict[str, Any]:
        self.root.mkdir(parents=True, exist_ok=True)
        report_id = _validate_id(str(report.get("report_id") or "unknown"))
        ts = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{ts}_{report_id}.json"
        path = _ensure_under_root(self.root / filename, self.root)
        entry = {
            "spooled_at": datetime.now(tz=UTC).replace(microsecond=0).isoformat(),
            "reason": reason,
            "node": node,
            "report": report,
        }
        _atomic_write(path, entry)
        return {"ok": True, "path": str(path), "filename": filename}

    def list_spooled_reports(self) -> dict[str, Any]:
        self.root.mkdir(parents=True, exist_ok=True)
        items: list[dict[str, Any]] = []
        for fp in sorted(self.root.glob("*.json")):
            if fp.is_symlink():
                continue
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                items.append({
                    "filename": fp.name,
                    "path": str(fp),
                    "spooled_at": data.get("spooled_at"),
                    "reason": data.get("reason"),
                    "report_id": (data.get("report") or {}).get("report_id"),
                })
            except (json.JSONDecodeError, OSError):
                continue
        return {"count": len(items), "items": items}

    def load_spooled(self, filename: str) -> dict[str, Any] | None:
        safe = _validate_id(filename.replace(".json", ""))
        path = _ensure_under_root(self.root / f"{safe}.json" if not filename.endswith(".json") else self.root / filename, self.root)
        if not path.is_file():
            for fp in self.root.glob("*.json"):
                if fp.name == filename:
                    path = _ensure_under_root(fp, self.root)
                    break
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def retry_spooled_reports(
        self,
        *,
        upload_fn,
    ) -> dict[str, Any]:
        listed = self.list_spooled_reports()
        results: list[dict[str, Any]] = []
        for item in listed.get("items") or []:
            fp = Path(str(item.get("path")))
            if not fp.is_file():
                continue
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                result = upload_fn(data.get("node") or {}, data.get("report") or {})
                if result.get("ok"):
                    fp.unlink(missing_ok=True)
                results.append({"filename": fp.name, "ok": result.get("ok"), "code": result.get("code")})
            except (json.JSONDecodeError, OSError, AgentSpoolError) as exc:
                results.append({"filename": fp.name, "ok": False, "error": str(exc)})
        return {"retried": len(results), "results": results}
