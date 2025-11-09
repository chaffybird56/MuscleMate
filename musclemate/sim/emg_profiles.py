"""
Scripted EMG profiles for demos and testing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import cycle
from time import time
from typing import Iterable, Iterator, List, Sequence, Tuple

from ..hardware.emg import EMGReader


@dataclass
class ScriptedEMGSource(EMGReader):
    """
    Generate deterministic EMG sequences based on time-stamped segments.
    """

    segments: Sequence[Tuple[Tuple[float, float], float]]
    repeat: bool = True
    _start: float = field(init=False, default=0.0)
    _iterator: Iterator[Tuple[Tuple[float, float], float]] = field(
        init=False, default=None  # type: ignore[assignment]
    )
    _current_value: Tuple[float, float] = field(
        init=False, default=(0.0, 0.0)
    )
    _segment_end: float = field(init=False, default=0.0)

    def __post_init__(self) -> None:
        self._reset_iterator()

    def _reset_iterator(self) -> None:
        sequence: Iterable = cycle(self.segments) if self.repeat else iter(self.segments)
        self._iterator = iter(sequence)
        self._start = time()
        self._segment_end = self._start

    def read(self) -> Tuple[float, float]:
        now = time()
        if now >= self._segment_end:
            try:
                (value, duration) = next(self._iterator)
            except StopIteration:
                if self.repeat:
                    self._reset_iterator()
                    (value, duration) = next(self._iterator)
                else:
                    return self._current_value
            self._current_value = value
            self._segment_end = now + max(duration, 0.0)
        return self._current_value


def scripted_cycle() -> ScriptedEMGSource:
    """Default scripted cycle that runs one complete sterilization sequence."""

    sequence: List[Tuple[Tuple[float, float], float]] = [
        ((0.0, 0.0), 0.5),  # rest
        ((0.9, 0.0), 0.2),  # start (select bin)
        ((0.0, 0.0), 0.2),
        ((0.9, 0.0), 0.2),  # cycle bin
        ((0.0, 0.0), 0.4),
        ((0.0, 0.9), 0.3),  # grip
        ((0.0, 0.0), 0.3),
        ((0.9, 0.9), 0.3),  # open door
        ((0.0, 0.0), 0.3),
        ((0.0, 0.9), 0.3),  # release
        ((0.0, 0.0), 0.5),
    ]
    return ScriptedEMGSource(sequence, repeat=True)

