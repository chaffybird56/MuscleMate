"""
Python motion sequences — build instructions for cross-functional handoff.

Sequences are data-driven, diffable in git, and runnable without the EMG FSM
for bench validation and manufacturing duty-cycle tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from time import sleep
from typing import List, Optional, Tuple

from hardware.arm import ArmInterface
from safety.interlocks import SafetySupervisor


class StepKind(Enum):
    MOVE = auto()
    GRIP_CLOSE = auto()
    GRIP_OPEN = auto()
    DWELL = auto()
    HOME = auto()
    CYCLE_MARK = auto()


@dataclass(frozen=True)
class MotionStep:
    kind: StepKind
    pose: Optional[Tuple[float, float, float]] = None
    speed: float = 0.4
    dwell_s: float = 0.0
    note: str = ""


@dataclass
class MotionSequence:
    name: str
    version: str
    steps: List[MotionStep]
    description: str = ""

    def step_count(self) -> int:
        return len(self.steps)


STERILIZATION_AUTOMATION = MotionSequence(
    name="sterilization_automation",
    version="1.0.0",
    description="Deterministic pick-transit-place for instrument sterilization duty cycle.",
    steps=[
        MotionStep(StepKind.HOME, note="safe start"),
        MotionStep(StepKind.MOVE, (0.30, 0.18, 0.08), 0.35, note="bin_a_approach"),
        MotionStep(StepKind.GRIP_CLOSE, note="grip_instrument"),
        MotionStep(StepKind.MOVE, (0.30, 0.18, 0.18), 0.45, note="lift_clear"),
        MotionStep(StepKind.MOVE, (0.45, -0.12, 0.12), 0.55, note="autoclave_transit"),
        MotionStep(StepKind.DWELL, dwell_s=0.4, note="door_interlock_settle"),
        MotionStep(StepKind.MOVE, (0.45, -0.12, 0.07), 0.35, note="place_insert"),
        MotionStep(StepKind.GRIP_OPEN, note="release_instrument"),
        MotionStep(StepKind.HOME, note="return_safe"),
        MotionStep(StepKind.CYCLE_MARK, note="duty_cycle_complete"),
    ],
)

MANUFACTURING_VALIDATION = MotionSequence(
    name="manufacturing_validation",
    version="1.0.0",
    description="Short loop for OEE-style timing and interlock stress on integration rigs.",
    steps=[
        MotionStep(StepKind.HOME, note="t0_home"),
        MotionStep(StepKind.MOVE, (0.32, 0.00, 0.10), 0.50, note="waypoint_1"),
        MotionStep(StepKind.MOVE, (0.40, -0.05, 0.14), 0.50, note="waypoint_2"),
        MotionStep(StepKind.GRIP_CLOSE, dwell_s=0.2, note="grip_verify"),
        MotionStep(StepKind.GRIP_OPEN, note="grip_release"),
        MotionStep(StepKind.HOME, note="t_end_home"),
        MotionStep(StepKind.CYCLE_MARK, note="validation_cycle"),
    ],
)


def run_sequence_on_arm(
    arm: ArmInterface,
    sequence: MotionSequence,
    safety: Optional[SafetySupervisor] = None,
    *,
    step_delay_s: float = 0.05,
) -> List[dict]:
    """Execute a motion sequence with optional interlock gating."""
    log: List[dict] = []
    for idx, step in enumerate(sequence.steps):
        if safety is not None and step.kind != StepKind.CYCLE_MARK:
            safety.require_motion(f"{sequence.name}:{step.note or step.kind.name}")

        if step.kind == StepKind.MOVE and step.pose:
            x, y, z = step.pose
            arm.move_pose(x, y, z, speed=step.speed)
        elif step.kind == StepKind.GRIP_CLOSE:
            arm.close_gripper()
            if step.dwell_s:
                sleep(step.dwell_s)
        elif step.kind == StepKind.GRIP_OPEN:
            arm.open_gripper()
        elif step.kind == StepKind.DWELL:
            sleep(step.dwell_s)
        elif step.kind == StepKind.HOME:
            arm.home()
        elif step.kind == StepKind.CYCLE_MARK and safety is not None:
            safety.duty.record_cycle_complete()

        log.append(
            {
                "index": idx,
                "kind": step.kind.name,
                "note": step.note,
                "pose": step.pose,
            }
        )
        sleep(step_delay_s)
    return log
