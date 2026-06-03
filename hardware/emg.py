"""
EMG acquisition interfaces.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Tuple


class EMGReader(Protocol):
    """Readable two-channel EMG source."""

    def read(self) -> Tuple[float, float]:
        """Return latest normalized EMG tuple in [0, 1]."""


@dataclass
class StaticEMGSource(EMGReader):
    """Fixed-value EMG source useful for unit tests and demos."""

    value: Tuple[float, float] = (0.0, 0.0)

    def read(self) -> Tuple[float, float]:
        return self.value

