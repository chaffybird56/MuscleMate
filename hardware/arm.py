"""
Hardware abstraction for arm control.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Tuple


class ArmInterface(Protocol):
    """Common interface for any robotic arm implementation."""

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
        """Move the arm to the target pose."""

    def open_gripper(self) -> None:
        """Open the gripper."""

    def close_gripper(self) -> None:
        """Close the gripper."""

    def home(self) -> None:
        """Return the arm to a safe home pose."""

    def read_pose(self) -> Tuple[float, float, float, float, float, float]:
        """Read the current pose."""


@dataclass
class QArmStub(ArmInterface):
    """
    Minimal in-memory stub that logs calls.

    Replace with Quanser QArm or simulation binding for production use.
    """

    pose: Tuple[float, float, float, float, float, float] = (0, 0, 0, 0, 0, 0)
    gripper_closed: bool = False

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
        self.pose = (x, y, z, yaw, pitch, roll)

    def open_gripper(self) -> None:
        self.gripper_closed = False

    def close_gripper(self) -> None:
        self.gripper_closed = True

    def home(self) -> None:
        self.pose = (0, 0, 0, 0, 0, 0)
        self.gripper_closed = False

    def read_pose(self) -> Tuple[float, float, float, float, float, float]:
        return self.pose

