# Remote Companion – Entwicklerleitfaden

Kurzanleitung, um ein **neues Remote-Modul** zu registrieren, mit Widgets, Aktionen und Eventbus-Events. Voraussetzung: [REMOTE_COMPANION.md](./REMOTE_COMPANION.md) (Architektur, API, Rollen) ist gelesen.

---

## 1. Modulvertrag (RemoteModule)

Jedes Modul muss das Protokoll in `backend/core/registry.py` erfüllen:

- **descriptor()** → `ModuleDescriptor`: id, name, description, widgets, actions.
- **get_state()** → `dict`: aktueller State (für GET `/api/modules/{id}/state`).
- **perform_action(action_id, payload)** → `dict`: `{ "success": bool, "message"?: str, "data"?: ... }`.
- **subscribe_topics()** → `List[str]`: Topics, die dieses Modul publiziert (für Doku/Filterung).

Modelle: `backend/models/module.py` (ModuleDescriptor), `widget.py` (WidgetDescriptor), `action.py` (ActionDescriptor, ActionInvocation, ActionResult).

---

## 2. Neues Modul anlegen

### 2.1 Service-Klasse

Neue Datei unter `backend/services/`, z. B. `mein_modul_service.py`:

```python
from typing import Any, List
from models.module import ModuleDescriptor
from models.widget import WidgetDescriptor
from models.action import ActionDescriptor

class MeinModulService:
    def __init__(self):
        self._state = {"value": 0}  # Ihr State

    def descriptor(self) -> ModuleDescriptor:
        return ModuleDescriptor(
            id="mein-modul",
            name="Mein Modul",
            description="Kurzbeschreibung",
            widgets=[
                WidgetDescriptor(id="main", type="StatusCard", label="Status"),
            ],
            actions=[
                ActionDescriptor(id="do_something", label="Aktion ausführen", params_schema={...}),
            ],
        )

    def get_state(self) -> dict[str, Any]:
        return dict(self._state)

    def perform_action(self, action_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        if action_id == "do_something":
            # Logik, State aktualisieren, ggf. Event publizieren
            return {"success": True, "message": "Erledigt", "data": {}}
        return {"success": False, "message": "Unbekannte Aktion"}

    def subscribe_topics(self) -> List[str]:
        return ["module.state.changed", "mein_modul.custom"]
```

### 2.2 In der Registry registrieren

In `backend/services/module_loader.py`:

- Import: `from services.mein_modul_service import MeinModulService`
- In `register_all()`: `reg.register(MeinModulService())`

Nach Neustart des Backends erscheint das Modul unter GET `/api/modules` und GET `/api/modules/mein-modul`; State unter GET `/api/modules/mein-modul/state`; Aktionen unter POST `/api/modules/mein-modul/actions/do_something`.

---

## 3. Widgets

Widgets sind reine Beschreibungen für das Frontend (welches UI-Element für welchen State/Aktion). Typen werden im Frontend interpretiert (z. B. `StatusCard`, `PresetGrid`, `VolumeSlider`, `EqControl`, `LogViewer`). Neue Widget-Typen: Frontend in `frontend/src/features/remote/components/` erweitern und in `ModulePage.tsx` nach `widget.type` verzweigen.

- **WidgetDescriptor:** id, type, label (optional weitere Felder je nach Bedarf).

---

## 4. Aktionen

- **ActionDescriptor:** id, label, optional params_schema (JSON-Schema für das Payload).
- **Aufruf:** POST `/api/modules/{module_id}/actions/{action_id}` mit Body `{ "payload": { ... } }`. Erfordert mindestens Rolle **controller** (viewer erhält 403).
- **Rückgabe:** `ActionResult`: success, message, data; kommt aus dem Rückgabe-dict von `perform_action()`.

---

## 5. Events publizieren

- **Eventbus:** `from core.eventbus import get_eventbus` → `get_eventbus().publish(topic, payload)`.
- **Topic-Namen:** In `backend/models/events.py` sind bekannte Topics in `EVENT_TOPICS` aufgeführt; eigene Topics können ergänzt werden. Typisch: nach Aktion/State-Änderung `module.state.changed` mit `{"module_id": "...", "state": ...}` und ggf. modulspezifische Topics (z. B. `tuner.volume_changed`).
- **Async-Kontext:** Wenn Sie aus synchronem Code (z. B. in `perform_action`) publizieren, muss der Eventbus asynchron laufen. Siehe `sabrina_tuner_service.py`: Nutzung einer Event-Loop und `create_task(eb.publish(...))`, falls die Loop bereits läuft.

Beispiel:

```python
from core.eventbus import get_eventbus

def _publish(topic: str, payload: dict) -> None:
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            get_eventbus().publish(topic, payload)  # bei neuerem asyncio: create_task
    except Exception:
        pass

# Nach State-Änderung:
_publish("module.state.changed", {"module_id": "mein-modul", "state": self.get_state()})
```

---

## 6. Tests

- **Unit-Tests:** `backend/tests/test_remote_registry.py` – Registry, get_descriptors, get_state, perform_action für vorhandene Module; gleiches Muster für ein neues Modul nutzbar.
- **Integration:** `test_remote_errors.py` prüft 401 ohne Session, 404 unbekanntes Modul, 403 bei Aktion als viewer. Eigene Modul-Integrationstests können analog mit TestClient und temporärer DB ergänzt werden.

Lauf: `cd backend && ./venv/bin/python -m unittest tests.test_remote_* -v`.

---

## 7. Kurz-Checkliste

1. Service-Klasse mit `descriptor()`, `get_state()`, `perform_action()`, `subscribe_topics()`.
2. In `module_loader.py` registrieren.
3. Optional: Events in `models/events.py` (EVENT_TOPICS) eintragen und im Service publizieren.
4. Optional: Neues Widget im Frontend anzeigen (neuer Typ in ModulePage + Komponente).
5. Backend neu starten (bzw. Service `pi-installer-backend` neu starten).

---

*Siehe auch: README_remote_architecture.md (ursprünglicher Plan), REMOTE_COMPANION.md (API & Rollen).*
