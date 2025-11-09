"""
Configuration dataclasses for MuscleMate.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Thresholds:
    """EMG signal thresholds and timing for gesture decoding."""

    emg_on: float = 0.65
    emg_off: float = 0.35
    deadband: float = 0.05
    debounce_s: float = 0.15
    cooldown_s: float = 0.35
    longpress_s: float = 1.20


@dataclass(frozen=True)
class Sampling:
    """Sampling configuration for the control loop."""

    loop_hz: float = 50.0
    runtime_s: float = 180.0


@dataclass(frozen=True)
class Speeds:
    """Speeds and dwell times for robot actions."""

    move: float = 0.6
    approach: float = 0.4
    retract: float = 0.6
    door: float = 0.3
    grip_time_s: float = 0.50


@dataclass(frozen=True)
class Waypoints:
    """Workspace waypoints for the sterilization flow."""

    home: Tuple[float, float, float] = (0.38, 0.00, 0.20)
    autoclave: Tuple[float, float, float] = (0.45, -0.12, 0.12)
    bins: Tuple[Tuple[float, float, float], ...] = (
        (0.30, 0.18, 0.08),
        (0.32, 0.00, 0.08),
        (0.30, -0.18, 0.08),
    )

