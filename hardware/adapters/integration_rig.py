"""
Integration rig adapter — same control stack, production-style interlock map.

Replace QArmStub / StaticEMGSource with vendor bindings in this module only;
bench commissioning checklist must pass before switching phase to integration.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from hardware.arm import ArmInterface, QArmStub
from hardware.emg import EMGReader, StaticEMGSource
from safety.interlocks import InterlockInputs, SafetySupervisor

from .base import AdapterPhase


@dataclass
class IntegrationRigAdapter:
    phase: AdapterPhase = AdapterPhase.INTEGRATION
    name: str = "integration-rig-v1"
    _connected: bool = False
    _bench_signoff_id: str = ""
    _arm: ArmInterface = field(default_factory=QArmStub)
    _emg: EMGReader = field(default_factory=StaticEMGSource)
    _safety: SafetySupervisor = field(default_factory=SafetySupervisor)

    def connect(self) -> None:
        if not self._bench_signoff_id:
            raise RuntimeError(
                "Integration rig requires bench sign-off. "
                "Set bench_signoff_id after commissioning/bench_checklist.yaml passes."
            )
        self._safety.inputs = InterlockInputs(
            estop_latched=False,
            door_closed=True,
            gripper_pressure_ok=True,
            light_curtain_clear=True,
            technician_enable=True,
            drive_power_ok=True,
        )
        self._connected = True

    def set_bench_signoff(self, signoff_id: str) -> None:
        self._bench_signoff_id = signoff_id

    def arm(self) -> ArmInterface:
        if not self._connected:
            self.connect()
        return self._arm

    def emg(self) -> EMGReader:
        return self._emg

    def safety(self) -> SafetySupervisor:
        return self._safety

    def commissioning_report(self) -> dict:
        return {
            "adapter": self.name,
            "phase": self.phase.value,
            "bench_signoff_id": self._bench_signoff_id,
            "connected": self._connected,
            "safety": self._safety.snapshot(),
        }
