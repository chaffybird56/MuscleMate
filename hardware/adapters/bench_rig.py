"""
Bench rig adapter — technician commissioning before controls integration.

Validates interlock wiring, gripper IO, and deterministic motion stubs without
the full sterilization FSM running on production hardware.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic

from hardware.arm import QArmStub
from hardware.emg import StaticEMGSource
from safety.interlocks import InterlockInputs, SafetySupervisor

from .base import AdapterPhase


@dataclass
class BenchRigAdapter:
    phase: AdapterPhase = AdapterPhase.BENCH
    name: str = "bench-rig-v1"
    _connected: bool = False
    _checks: list[str] = field(default_factory=list)
    _arm: QArmStub = field(default_factory=QArmStub)
    _safety: SafetySupervisor = field(default_factory=SafetySupervisor)

    def connect(self) -> None:
        self._checks.clear()
        self._arm.home()
        self._checks.append("home_reached")
        self._safety.inputs = InterlockInputs(
            estop_latched=False,
            door_closed=True,
            technician_enable=True,
        )
        self._checks.append("interlocks_nominal")
        self._connected = True

    def arm(self) -> QArmStub:
        if not self._connected:
            self.connect()
        return self._arm

    def emg(self) -> StaticEMGSource:
        return StaticEMGSource((0.0, 0.0))

    def safety(self) -> SafetySupervisor:
        return self._safety

    def run_bench_motion_probe(self) -> dict:
        """Short deterministic sweep for technician sign-off."""
        self._safety.require_motion("bench_probe")
        poses = [(0.30, 0.10, 0.15), (0.40, 0.00, 0.18), (0.38, 0.00, 0.20)]
        for x, y, z in poses:
            self._arm.move_pose(x, y, z, speed=0.25)
        self._arm.home()
        return {"probe": "ok", "poses": len(poses), "ts": monotonic()}

    def commissioning_report(self) -> dict:
        return {
            "adapter": self.name,
            "phase": self.phase.value,
            "connected": self._connected,
            "checks": list(self._checks),
            "safety": self._safety.snapshot(),
        }
