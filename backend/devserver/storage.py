"""Dateibasierte Persistenz für den Development Server."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

UTC = timezone.utc


class DevServerStorageError(Exception):
    pass


def _validate_id(value: str, field: str) -> str:
    s = (value or "").strip()
    if not s or len(s) > 128:
        raise DevServerStorageError(f"invalid_{field}")
    for bad in ("..", "/", "\\"):
        if bad in s:
            raise DevServerStorageError(f"invalid_{field}")
    if s.startswith("."):
        raise DevServerStorageError(f"invalid_{field}")
    return s


def _ensure_under_root(path: Path, root: Path) -> Path:
    root_res = root.resolve()
    if path.is_symlink():
        raise DevServerStorageError("symlink_blocked")
    try:
        resolved = path.resolve()
    except OSError as exc:
        raise DevServerStorageError("path_resolve_failed") from exc
    root_s = str(root_res)
    resolved_s = str(resolved)
    if resolved_s != root_s and not resolved_s.startswith(root_s + os.sep):
        raise DevServerStorageError("path_traversal")
    return resolved


def _atomic_write_json(path: Path, data: dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise DevServerStorageError("symlink_blocked")
    tmp = path.with_name(path.name + ".tmp")
    if tmp.exists() and tmp.is_symlink():
        raise DevServerStorageError("symlink_blocked")
    content = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


class DevServerStorage:
    def __init__(self, storage_root: Path) -> None:
        self.root = storage_root.resolve()
        self.nodes_dir = self.root / "nodes"
        self.reports_dir = self.root / "reports"
        self.actions_dir = self.root / "actions"
        self.latest_dir = self.root / "latest"
        self.audit_dir = self.root / "audit"
        self.audit_file = self.audit_dir / "dev_server_events.jsonl"

    def _entity_path(self, subdir: Path, entity_id: str) -> Path:
        safe = _validate_id(entity_id, "entity_id")
        return _ensure_under_root(subdir / f"{safe}.json", self.root)

    def ensure_layout(self) -> None:
        for d in (self.nodes_dir, self.reports_dir, self.actions_dir, self.latest_dir, self.audit_dir):
            d.mkdir(parents=True, exist_ok=True)

    def save_node(self, node: dict[str, Any]) -> None:
        node_id = _validate_id(str(node.get("node_id") or ""), "node_id")
        path = self._entity_path(self.nodes_dir, node_id)
        _atomic_write_json(path, node)
        self.build_nodes_summary()

    def load_node(self, node_id: str) -> dict[str, Any] | None:
        path = self._entity_path(self.nodes_dir, node_id)
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list_nodes(self) -> list[dict[str, Any]]:
        self.ensure_layout()
        out: list[dict[str, Any]] = []
        for fp in sorted(self.nodes_dir.glob("*.json")):
            if fp.is_symlink():
                continue
            try:
                out.append(json.loads(fp.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue
        return out

    def save_report(self, report: dict[str, Any]) -> None:
        report_id = _validate_id(str(report.get("report_id") or ""), "report_id")
        path = self._entity_path(self.reports_dir, report_id)
        _atomic_write_json(path, report)
        self.build_reports_summary()

    def load_report(self, report_id: str) -> dict[str, Any] | None:
        path = self._entity_path(self.reports_dir, report_id)
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list_reports(self, *, limit: int = 100, node_id: str | None = None) -> list[dict[str, Any]]:
        self.ensure_layout()
        items: list[dict[str, Any]] = []
        for fp in sorted(self.reports_dir.glob("*.json"), reverse=True):
            if fp.is_symlink():
                continue
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if node_id and data.get("node_id") != node_id:
                continue
            items.append(data)
            if len(items) >= limit:
                break
        return items

    def save_action(self, action: dict[str, Any]) -> None:
        action_id = _validate_id(str(action.get("action_id") or ""), "action_id")
        path = self._entity_path(self.actions_dir, action_id)
        _atomic_write_json(path, action)
        self.build_actions_summary()

    def load_action(self, action_id: str) -> dict[str, Any] | None:
        path = self._entity_path(self.actions_dir, action_id)
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list_actions(self, *, limit: int = 100, node_id: str | None = None) -> list[dict[str, Any]]:
        self.ensure_layout()
        items: list[dict[str, Any]] = []
        for fp in sorted(self.actions_dir.glob("*.json"), reverse=True):
            if fp.is_symlink():
                continue
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if node_id and data.get("node_id") != node_id:
                continue
            items.append(data)
            if len(items) >= limit:
                break
        return items

    def append_audit_event(self, event: dict[str, Any]) -> None:
        self.ensure_layout()
        if self.audit_file.is_symlink():
            raise DevServerStorageError("symlink_blocked")
        line = json.dumps(event, sort_keys=True, ensure_ascii=False) + "\n"
        with self.audit_file.open("a", encoding="utf-8") as fh:
            fh.write(line)

    def build_nodes_summary(self) -> dict[str, Any]:
        nodes = self.list_nodes()
        summary = {
            "generated_at": datetime.now(tz=UTC).replace(microsecond=0).isoformat(),
            "count": len(nodes),
            "nodes": [
                {
                    "node_id": n.get("node_id"),
                    "display_name": n.get("display_name"),
                    "status": n.get("status"),
                    "last_seen_at": n.get("last_seen_at"),
                    "node_kind": n.get("node_kind"),
                }
                for n in nodes
            ],
        }
        _atomic_write_json(self.latest_dir / "nodes_summary.json", summary)
        return summary

    def build_reports_summary(self) -> dict[str, Any]:
        reports = self.list_reports(limit=200)
        summary = {
            "generated_at": datetime.now(tz=UTC).replace(microsecond=0).isoformat(),
            "count": len(reports),
            "reports": [
                {
                    "report_id": r.get("report_id"),
                    "node_id": r.get("node_id"),
                    "report_type": r.get("report_type"),
                    "created_at": r.get("created_at"),
                    "redaction_status": r.get("redaction_status"),
                }
                for r in reports[:50]
            ],
        }
        _atomic_write_json(self.latest_dir / "reports_summary.json", summary)
        return summary

    def build_actions_summary(self) -> dict[str, Any]:
        actions = self.list_actions(limit=200)
        summary = {
            "generated_at": datetime.now(tz=UTC).replace(microsecond=0).isoformat(),
            "count": len(actions),
            "actions": [
                {
                    "action_id": a.get("action_id"),
                    "node_id": a.get("node_id"),
                    "action_type": a.get("action_type"),
                    "status": a.get("status"),
                    "requested_at": a.get("requested_at"),
                }
                for a in actions[:50]
            ],
        }
        _atomic_write_json(self.latest_dir / "actions_summary.json", summary)
        return summary

    def reports_last_24h_count(self) -> int:
        cutoff = datetime.now(tz=UTC) - timedelta(hours=24)
        count = 0
        for r in self.list_reports(limit=500):
            created = str(r.get("created_at") or "")
            try:
                ts = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=UTC)
            except ValueError:
                continue
            if ts >= cutoff:
                count += 1
        return count

    def storage_ok(self) -> bool:
        try:
            self.ensure_layout()
            probe = self.latest_dir / ".storage_probe"
            _atomic_write_json(probe, {"ok": True})
            probe.unlink(missing_ok=True)
            return True
        except (DevServerStorageError, OSError):
            return False
