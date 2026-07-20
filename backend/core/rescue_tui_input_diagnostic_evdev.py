"""Passive Linux evdev reader (read-only, no exclusive grab, no injection)."""

from __future__ import annotations

import os
import select
import struct
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Iterable

from core.rescue_tui_input_diagnostic_contract import (
    EV_KEY,
    INPUT_EVENT_FMT_32,
    INPUT_EVENT_FMT_64,
    INPUT_EVENT_SIZE_32,
    INPUT_EVENT_SIZE_64,
    KEY_CODES,
)


@dataclass
class ParsedKeyEvent:
    timestamp_monotonic: float
    event_node: str
    type: int
    code: int
    name: str
    value: int
    device_class: str = "unknown"


def parse_input_event_bytes(
    blob: bytes,
    *,
    event_node: str = "",
    device_class: str = "unknown",
    word_size: int | None = None,
) -> list[ParsedKeyEvent]:
    """Parse complete input_event records; leftover bytes are ignored (partial read safe)."""
    if word_size == 4:
        fmt, size = INPUT_EVENT_FMT_32, INPUT_EVENT_SIZE_32
    elif word_size == 8:
        fmt, size = INPUT_EVENT_FMT_64, INPUT_EVENT_SIZE_64
    else:
        # Prefer native: on 64-bit host use 24-byte records.
        fmt, size = (INPUT_EVENT_FMT_64, INPUT_EVENT_SIZE_64) if struct.calcsize("l") == 8 else (
            INPUT_EVENT_FMT_32,
            INPUT_EVENT_SIZE_32,
        )

    out: list[ParsedKeyEvent] = []
    offset = 0
    now = time.monotonic()
    while offset + size <= len(blob):
        chunk = blob[offset : offset + size]
        offset += size
        try:
            _sec, _usec, etype, code, value = struct.unpack(fmt, chunk)
        except struct.error:
            break
        if etype != EV_KEY:
            continue
        name = KEY_CODES.get(int(code), f"KEY_{int(code)}")
        out.append(
            ParsedKeyEvent(
                timestamp_monotonic=now,
                event_node=event_node,
                type=int(etype),
                code=int(code),
                name=name,
                value=int(value),
                device_class=device_class,
            )
        )
    return out


def event_to_dict(ev: ParsedKeyEvent) -> dict[str, Any]:
    return {
        "timestamp_monotonic": ev.timestamp_monotonic,
        "event_node": ev.event_node,
        "device_class": ev.device_class,
        "type": "EV_KEY",
        "code": ev.code,
        "name": ev.name,
        "value": ev.value,
    }


class PassiveEvdevMonitor:
    """Open event nodes O_RDONLY|O_NONBLOCK; never grab."""

    def __init__(self, nodes: Iterable[str], *, class_by_node: dict[str, str] | None = None) -> None:
        self._class_by_node = class_by_node or {}
        self._fds: dict[int, tuple[str, BinaryIO]] = {}
        for node in nodes:
            path = Path(node)
            if not path.exists():
                continue
            try:
                fd = os.open(str(path), os.O_RDONLY | os.O_NONBLOCK)
            except OSError:
                continue
            # wrap as file object for select convenience
            fobj = os.fdopen(fd, "rb", buffering=0)
            self._fds[fd] = (str(path), fobj)

    def close(self) -> None:
        for _fd, (_node, fobj) in list(self._fds.items()):
            try:
                fobj.close()
            except OSError:
                pass
        self._fds.clear()

    def __enter__(self) -> PassiveEvdevMonitor:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def poll(self, timeout_s: float = 0.2) -> list[ParsedKeyEvent]:
        if not self._fds:
            return []
        rlist = [fobj for _n, fobj in self._fds.values()]
        ready, _, _ = select.select(rlist, [], [], max(0.0, timeout_s))
        events: list[ParsedKeyEvent] = []
        for fobj in ready:
            node = next((n for n, f in self._fds.values() if f is fobj), "")
            try:
                blob = fobj.read(4096) or b""
            except OSError:
                continue
            if not blob:
                continue
            cls = self._class_by_node.get(node, "unknown")
            events.extend(parse_input_event_bytes(blob, event_node=node, device_class=cls))
        return events

    def collect_until(
        self,
        *,
        wanted_names: set[str],
        timeout_s: float,
        only_press: bool = True,
    ) -> list[ParsedKeyEvent]:
        deadline = time.monotonic() + max(0.1, timeout_s)
        got: list[ParsedKeyEvent] = []
        seen: set[str] = set()
        while time.monotonic() < deadline and not wanted_names.issubset(seen):
            for ev in self.poll(0.2):
                if only_press and ev.value != 1:
                    continue
                got.append(ev)
                if ev.name in wanted_names:
                    seen.add(ev.name)
        return got

