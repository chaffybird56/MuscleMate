"""Digital-twin style JSONL trace for cycle analytics and handoff."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from time import time
from typing import Any, Optional

from .state_machine import ControllerEvent


class TraceWriter:
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path
        self._fh = open(path, "a", encoding="utf-8") if path else None

    def emit(self, event_type: str, payload: Any) -> None:
        row = {"ts": time(), "type": event_type, "payload": self._serialize(payload)}
        line = json.dumps(row, separators=(",", ":"))
        if self._fh:
            self._fh.write(line + "\n")
            self._fh.flush()

    def close(self) -> None:
        if self._fh:
            self._fh.close()
            self._fh = None

    @staticmethod
    def _serialize(obj: Any) -> Any:
        if isinstance(obj, ControllerEvent):
            return {
                "state": obj.state.name,
                "intent": obj.intent.name,
                "selected_bin": obj.selected_bin,
                "door_open": obj.door_open,
                "last_grip_closed": obj.last_grip_closed,
            }
        if is_dataclass(obj):
            return asdict(obj)
        if hasattr(obj, "name"):
            return obj.name
        return obj
