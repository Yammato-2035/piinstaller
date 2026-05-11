"""
PI-Installer-Modul: State, Aktionen, Eventbus.
State: job_status, progress, stage, last_logs, error.
Actions: start_job, cancel_job, fetch_logs.
Publiziert: job.progress, log.line, module.state.changed.
"""

import logging
from typing import Any, List

from core.eventbus import publish_fire_and_forget
from models.module import ModuleDescriptor
from models.widget import WidgetDescriptor
from models.action import ActionDescriptor

logger = logging.getLogger(__name__)


class PiInstallerService:
    """Remote-Modul PI-Installer: in-memory State (Stub), Aktionen, Events."""

    def __init__(self) -> None:
        self._state: dict[str, Any] = {
            "job_status": "idle",
            "progress": 0,
            "stage": "",
            "last_logs": [],
            "error": None,
        }

    def descriptor(self) -> ModuleDescriptor:
        return ModuleDescriptor(
            id="pi-installer",
            name="PI-Installer",
            description="Installations-Jobs, Fortschritt, Logs",
            widgets=[
                WidgetDescriptor(id="job_status", type="StatusCard", label="Job-Status"),
                WidgetDescriptor(id="logs", type="LogViewer", label="Logs"),
            ],
            actions=[
                ActionDescriptor(id="start_job", label="Job starten"),
                ActionDescriptor(id="cancel_job", label="Job abbrechen"),
                ActionDescriptor(id="fetch_logs", label="Logs abrufen"),
            ],
        )

    def get_state(self) -> dict[str, Any]:
        return {
            "job_status": self._state["job_status"],
            "progress": self._state["progress"],
            "stage": self._state["stage"],
            "last_logs": list(self._state["last_logs"][-50:]),  # letzte 50
            "error": self._state["error"],
        }

    def _append_log(self, line: str) -> None:
        self._state["last_logs"].append(line)
        if len(self._state["last_logs"]) > 200:
            self._state["last_logs"] = self._state["last_logs"][-100:]
        publish_fire_and_forget("log.line", {"line": line, "module_id": "pi-installer"})

    def perform_action(self, action_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if action_id == "start_job":
            if self._state["job_status"] == "running":
                return {"success": False, "message": "Job läuft bereits"}
            self._state["job_status"] = "running"
            self._state["progress"] = 0
            self._state["stage"] = "Gestartet"
            self._state["error"] = None
            self._append_log("[Remote] Job gestartet (Stub)")
            publish_fire_and_forget("job.progress", {"progress": 0, "stage": self._state["stage"], "job_status": "running"})
            publish_fire_and_forget("module.state.changed", {"module_id": "pi-installer", "state": self.get_state()})
            return {"success": True, "message": "Job gestartet (Stub)", "data": {"job_status": "running"}}
        if action_id == "cancel_job":
            if self._state["job_status"] != "running":
                return {"success": True, "message": "Kein laufender Job", "data": {}}
            self._state["job_status"] = "cancelled"
            self._state["stage"] = "Abgebrochen"
            self._append_log("[Remote] Job abgebrochen (Stub)")
            publish_fire_and_forget("job.progress", {"progress": self._state["progress"], "stage": self._state["stage"], "job_status": "cancelled"})
            publish_fire_and_forget("module.state.changed", {"module_id": "pi-installer", "state": self.get_state()})
            return {"success": True, "message": "Job abgebrochen", "data": {"job_status": "cancelled"}}
        if action_id == "fetch_logs":
            logs = list(self._state["last_logs"][-50:])
            return {"success": True, "message": "Logs", "data": {"logs": logs}}
        return {"success": False, "message": f"Unbekannte Aktion: {action_id}"}

    def subscribe_topics(self) -> List[str]:
        return ["job.progress", "log.line", "module.state.changed"]
