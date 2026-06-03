from __future__ import annotations

from enum import Enum
from typing import Protocol

from hardware.arm import ArmInterface
from hardware.emg import EMGReader
from safety.interlocks import InterlockInputs, SafetySupervisor


class AdapterPhase(str, Enum):
    BENCH = "bench"
    INTEGRATION = "integration"


class HardwareAdapter(Protocol):
    """Swap arm/EMG/interlock wiring without changing control software."""

    phase: AdapterPhase
    name: str

    def connect(self) -> None:
        """Run bring-up checks (technician-led on bench rigs)."""

    def arm(self) -> ArmInterface:
        ...

    def emg(self) -> EMGReader:
        ...

    def safety(self) -> SafetySupervisor:
        ...

    def commissioning_report(self) -> dict:
        """Structured handoff payload for controls/software partners."""
