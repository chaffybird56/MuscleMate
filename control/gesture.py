"""
Gesture decoding for MuscleMate.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from time import time
from typing import List, Optional

from .config import Thresholds


class Intent(Enum):
    """High-level intent commands triggered by gestures."""

    NONE = auto()
    START = auto()
    GRIP = auto()
    RELEASE = auto()
    OPEN_DOOR = auto()
    CLOSE_DOOR = auto()
    ABORT = auto()


@dataclass
class GestureDecoder:
    """
    Decode two-channel EMG into Intent values with hysteresis, debounce,
    cooldown, and long-press detection.
    """

    thresholds: Thresholds
    _active: List[bool] = None  # type: ignore[assignment]
    _t_change: List[float] = None  # type: ignore[assignment]
    _press_start: List[Optional[float]] = None  # type: ignore[assignment]
    _last_intent_time: float = 0.0

    def __post_init__(self) -> None:
        self._active = [False, False]
        self._t_change = [0.0, 0.0]
        self._press_start = [None, None]

    def update(self, ch1: float, ch2: float) -> None:
        now = time()
        for idx, value in enumerate((ch1, ch2)):
            value = 0.0 if abs(value) < self.thresholds.deadband else value
            if not self._active[idx] and value >= self.thresholds.emg_on:
                self._active[idx] = True
                self._t_change[idx] = now
                self._press_start[idx] = now
            elif self._active[idx] and value <= self.thresholds.emg_off:
                self._active[idx] = False
                self._t_change[idx] = now
                self._press_start[idx] = None

    def intent(self) -> Intent:
        now = time()
        if now - self._last_intent_time < self.thresholds.cooldown_s:
            return Intent.NONE

        if (
            self._press_start[1] is not None
            and now - self._press_start[1] >= self.thresholds.longpress_s
        ):
            self._last_intent_time = now
            return Intent.ABORT

        active = [
            self._active[i] and (now - self._t_change[i] >= self.thresholds.debounce_s)
            for i in (0, 1)
        ]

        if active[0] and not active[1]:
            self._last_intent_time = now
            return Intent.START
        if active[1] and not active[0]:
            self._last_intent_time = now
            return Intent.GRIP
        if active[0] and active[1]:
            self._last_intent_time = now
            return Intent.OPEN_DOOR
        return Intent.NONE

