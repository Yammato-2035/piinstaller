"""
Sabrina-Tuner-Modul (DSI-Radio): State, Aktionen, Eventbus.
State: station, volume, muted, now_playing, eq.
Actions: play_preset, set_volume, mute_toggle, set_eq.
Publiziert: tuner.now_playing, tuner.volume_changed (und ggf. module.state.changed).
"""

import asyncio
import logging
from typing import Any, List

from core.eventbus import get_eventbus
from models.module import ModuleDescriptor
from models.widget import WidgetDescriptor
from models.action import ActionDescriptor

logger = logging.getLogger(__name__)


def _publish(topic: str, payload: dict[str, Any]) -> None:
    """Fire-and-forget Eventbus-Publish (async aus sync Kontext)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            eb = get_eventbus()
            loop.create_task(eb.publish(topic, payload))
    except Exception as e:
        logger.debug("Eventbus publish %s: %s", topic, e)


class SabrinaTunerService:
    """Remote-Modul Sabrina Tuner: in-memory State, Aktionen, Events."""

    def __init__(self) -> None:
        self._state: dict[str, Any] = {
            "station": None,
            "volume": 80,
            "muted": False,
            "now_playing": None,
            "eq": {},
        }

    def descriptor(self) -> ModuleDescriptor:
        return ModuleDescriptor(
            id="sabrina-tuner",
            name="Sabrina Tuner",
            description="DSI-Radio: Sender, Lautstärke, Now Playing",
            widgets=[
                WidgetDescriptor(id="status", type="StatusCard", label="Status"),
                WidgetDescriptor(id="presets", type="PresetGrid", label="Presets"),
                WidgetDescriptor(id="volume", type="VolumeSlider", label="Lautstärke"),
                WidgetDescriptor(id="eq", type="EqControl", label="EQ"),
            ],
            actions=[
                ActionDescriptor(id="play_preset", label="Preset abspielen", params_schema={"type": "object", "properties": {"preset_id": {"type": "string"}}}),
                ActionDescriptor(id="set_volume", label="Lautstärke setzen", params_schema={"type": "object", "properties": {"value": {"type": "number"}}}),
                ActionDescriptor(id="mute_toggle", label="Stummschaltung"),
                ActionDescriptor(id="set_eq", label="EQ setzen"),
            ],
        )

    def get_state(self) -> dict[str, Any]:
        return dict(self._state)

    def perform_action(self, action_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if action_id == "play_preset":
            preset_id = (payload or {}).get("preset_id") or ""
            self._state["station"] = preset_id or self._state.get("station")
            self._state["now_playing"] = {"preset": preset_id, "title": preset_id or "Live"}
            _publish("tuner.now_playing", {"station": self._state["station"], "now_playing": self._state["now_playing"]})
            _publish("module.state.changed", {"module_id": "sabrina-tuner", "state": self.get_state()})
            return {"success": True, "message": "Preset gewechselt", "data": {"preset_id": preset_id}}
        if action_id == "set_volume":
            try:
                v = int((payload or {}).get("value", self._state["volume"]))
                v = max(0, min(100, v))
            except (TypeError, ValueError):
                v = self._state["volume"]
            self._state["volume"] = v
            _publish("tuner.volume_changed", {"volume": v, "muted": self._state["muted"]})
            _publish("module.state.changed", {"module_id": "sabrina-tuner", "state": self.get_state()})
            return {"success": True, "message": f"Lautstärke {v}", "data": {"volume": v}}
        if action_id == "mute_toggle":
            self._state["muted"] = not self._state.get("muted", False)
            _publish("tuner.volume_changed", {"volume": self._state["volume"], "muted": self._state["muted"]})
            _publish("module.state.changed", {"module_id": "sabrina-tuner", "state": self.get_state()})
            return {"success": True, "message": "Stumm" if self._state["muted"] else "An", "data": {"muted": self._state["muted"]}}
        if action_id == "set_eq":
            eq = (payload or {}).get("eq")
            if isinstance(eq, dict):
                self._state["eq"] = dict(eq)
            _publish("module.state.changed", {"module_id": "sabrina-tuner", "state": self.get_state()})
            return {"success": True, "message": "EQ aktualisiert", "data": {"eq": self._state["eq"]}}
        return {"success": False, "message": f"Unbekannte Aktion: {action_id}"}

    def subscribe_topics(self) -> List[str]:
        return ["tuner.now_playing", "tuner.volume_changed", "module.state.changed"]
