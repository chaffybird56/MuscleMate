"""
Finite state machine for the sterilization workflow.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from time import sleep
from typing import Optional, Tuple

from .config import Speeds, Thresholds, Waypoints
from hardware.arm import ArmInterface
from hardware.emg import EMGReader
from .utils import clamp
from .gesture import GestureDecoder, Intent


class State(Enum):
    """Controller states."""

    IDLE = auto()
    SELECT_BIN = auto()
    APPROACH = auto()
    GRIP = auto()
    LIFT = auto()
    TRANSIT = auto()
    OPEN_AUTOCLAVE = auto()
    PLACE = auto()
    CLOSE_AUTOCLAVE = auto()
    HOME = auto()
    ABORT = auto()


@dataclass
class ControllerEvent:
    """Event log emitted after each tick."""

    state: State
    intent: Intent
    selected_bin: int
    door_open: bool
    last_grip_closed: bool


@dataclass
class SterilizationController:
    """
    Core controller that advances the workflow based on decoded intents.
    """

    arm: ArmInterface
    emg: EMGReader
    thresholds: Thresholds
    waypoints: Waypoints
    speeds: Speeds
    state: State = State.IDLE
    selected_bin: int = 0
    door_open: bool = False
    _last_grip_action_close: bool = False
    _decoder: Optional[GestureDecoder] = None

    def __post_init__(self) -> None:
        self._decoder = GestureDecoder(self.thresholds)

    @property
    def decoder(self) -> GestureDecoder:
        assert self._decoder is not None
        return self._decoder

    def move_to(self, xyz: Tuple[float, float, float], speed: float) -> None:
        x, y, z = xyz
        self.arm.move_pose(x, y, z, speed=clamp(speed, 0.1, 1.0))

    def grip(self, close: bool) -> None:
        (self.arm.close_gripper if close else self.arm.open_gripper)()
        sleep(self.speeds.grip_time_s)
        self._last_grip_action_close = close

    def toggle_door(self) -> None:
        sleep(0.4 if not self.door_open else 0.3)
        self.door_open = not self.door_open

    def tick(self) -> ControllerEvent:
        ch1, ch2 = self.emg.read()
        self.decoder.update(ch1, ch2)
        intent = self.decoder.intent()

        if intent == Intent.ABORT:
            self.state = State.ABORT

        if self.state == State.IDLE:
            if intent == Intent.START:
                self.state = State.SELECT_BIN

        elif self.state == State.SELECT_BIN:
            if intent == Intent.START:
                self.selected_bin = (self.selected_bin + 1) % len(self.waypoints.bins)
            elif intent == Intent.GRIP:
                self.state = State.APPROACH

        elif self.state == State.APPROACH:
            self.move_to(self.waypoints.bins[self.selected_bin], self.speeds.approach)
            self.state = State.GRIP

        elif self.state == State.GRIP:
            if intent == Intent.GRIP:
                self.grip(close=True)
                self.state = State.LIFT

        elif self.state == State.LIFT:
            x, y, z = self.waypoints.bins[self.selected_bin]
            self.move_to((x, y, z + 0.10), self.speeds.retract)
            self.state = State.TRANSIT

        elif self.state == State.TRANSIT:
            self.move_to(self.waypoints.autoclave, self.speeds.move)
            self.state = State.OPEN_AUTOCLAVE

        elif self.state == State.OPEN_AUTOCLAVE:
            if intent == Intent.OPEN_DOOR:
                self.toggle_door()
                self.state = State.PLACE

        elif self.state == State.PLACE:
            ax, ay, az = self.waypoints.autoclave
            self.move_to((ax, ay, az - 0.05), self.speeds.approach)
            if intent == Intent.GRIP and self._last_grip_action_close:
                self.grip(close=False)
                self.state = State.CLOSE_AUTOCLAVE

        elif self.state == State.CLOSE_AUTOCLAVE:
            if self.door_open and intent == Intent.OPEN_DOOR:
                self.toggle_door()
                self.state = State.HOME

        elif self.state == State.HOME:
            self.move_to(self.waypoints.home, self.speeds.move)
            self.state = State.IDLE

        elif self.state == State.ABORT:
            try:
                self.arm.home()
            finally:
                self.state = State.IDLE

        return ControllerEvent(
            state=self.state,
            intent=intent,
            selected_bin=self.selected_bin,
            door_open=self.door_open,
            last_grip_closed=self._last_grip_action_close,
        )

