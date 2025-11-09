"""
High-level orchestration for MuscleMate controller.
"""

from __future__ import annotations

from time import sleep, time
from typing import Optional, Protocol

from .config import Sampling
from .state_machine import ControllerEvent, SterilizationController


class EventSink(Protocol):
    def append(self, event: ControllerEvent) -> None:
        ...


def run_controller(
    controller: SterilizationController,
    sampling: Sampling,
    *,
    event_sink: Optional[EventSink] = None,
) -> None:
    """
    Execute the main control loop.

    Args:
        controller: Configured SterilizationController instance.
        sampling: Loop timing configuration.
        event_sink: Optional iterable to collect ControllerEvent outputs.
    """

    start = time()
    dt = 1.0 / max(1.0, sampling.loop_hz)
    while time() - start < sampling.runtime_s:
        event = controller.tick()
        if event_sink is not None:
            event_sink.append(event)
        sleep(dt)

