"""Arm wrapper enforcing interlocks and deterministic speed clamps."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from safety.interlocks import SafetySupervisor

from .arm import ArmInterface


@dataclass
class MotionRecord:
    kind: str
    target: Tuple[float, ...]
    speed: float


@dataclass
class SafeguardedArm:
    inner: ArmInterface
    safety: SafetySupervisor
    max_speed: float = 0.85
    motion_log: List[MotionRecord] = field(default_factory=list)

    def move_pose(
        self,
        x: float,
        y: float,
        z: float,
        yaw: float = 0.0,
        pitch: float = 0.0,
        roll: float = 0.0,
        speed: float = 0.5,
    ) -> None:
        self.safety.require_motion("move_pose")
        spd = min(max(speed, 0.1), self.max_speed)
        self.motion_log.append(MotionRecord("move_pose", (x, y, z, yaw, pitch, roll), spd))
        self.inner.move_pose(x, y, z, yaw=yaw, pitch=pitch, roll=roll, speed=spd)

    def open_gripper(self) -> None:
        self.safety.require_motion("open_gripper")
        self.motion_log.append(MotionRecord("open_gripper", (), 0.0))
        self.inner.open_gripper()

    def close_gripper(self) -> None:
        self.safety.require_motion("close_gripper")
        self.motion_log.append(MotionRecord("close_gripper", (), 0.0))
        self.inner.close_gripper()

    def home(self) -> None:
        self.motion_log.append(MotionRecord("home", (), 0.0))
        self.inner.home()

    def read_pose(self) -> Tuple[float, float, float, float, float, float]:
        return self.inner.read_pose()
