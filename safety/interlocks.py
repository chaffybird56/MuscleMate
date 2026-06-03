"""
Manufacturing-style safety interlocks and duty-cycle policy.

Guards deterministic motion: no move unless E-stop cleared, door/gripper
safeguarding satisfied, and duty-cycle limits allow the next cycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic
from typing import Optional


class SafetyFault(Exception):
    """Raised when a motion command violates an active interlock."""


@dataclass(frozen=True)
class InterlockInputs:
    """Digital inputs from bench or integration rig I/O."""

    estop_latched: bool = False
    door_closed: bool = True
    gripper_pressure_ok: bool = True
    light_curtain_clear: bool = True
    technician_enable: bool = True
    drive_power_ok: bool = True


@dataclass
class DutyCyclePolicy:
    """Manufacturing-style run limits (continuous operation envelope)."""

    max_cycles_per_hour: int = 120
    min_cycle_gap_s: float = 2.0
    max_continuous_runtime_s: float = 3600.0
    _cycle_times: list[float] = field(default_factory=list)
    _session_start: float = field(default_factory=monotonic)

    def record_cycle_complete(self) -> None:
        now = monotonic()
        self._cycle_times.append(now)
        cutoff = now - 3600.0
        self._cycle_times = [t for t in self._cycle_times if t >= cutoff]

    def allow_new_cycle(self) -> tuple[bool, str]:
        now = monotonic()
        if now - self._session_start > self.max_continuous_runtime_s:
            return False, "max_continuous_runtime exceeded"
        if self._cycle_times:
            if now - self._cycle_times[-1] < self.min_cycle_gap_s:
                return False, "min_cycle_gap not met"
            recent = [t for t in self._cycle_times if t >= now - 3600.0]
            if len(recent) >= self.max_cycles_per_hour:
                return False, "max_cycles_per_hour exceeded"
        return True, "ok"


@dataclass
class SafetySupervisor:
    """
    Central safety gate for all arm motion and sterilization cycles.
    """

    inputs: InterlockInputs = field(default_factory=InterlockInputs)
    duty: DutyCyclePolicy = field(default_factory=DutyCyclePolicy)
    _fault_latched: bool = False
    _last_fault: str = ""

    def motion_allowed(self) -> bool:
        if self._fault_latched:
            return False
        i = self.inputs
        return (
            not i.estop_latched
            and i.door_closed
            and i.gripper_pressure_ok
            and i.light_curtain_clear
            and i.technician_enable
            and i.drive_power_ok
        )

    def require_motion(self, context: str = "move") -> None:
        if not self.motion_allowed():
            self._fault_latched = True
            self._last_fault = f"interlock block: {context}"
            raise SafetyFault(self._last_fault)

    def require_cycle_start(self) -> None:
        ok, reason = self.duty.allow_new_cycle()
        if not ok:
            self._fault_latched = True
            self._last_fault = f"duty cycle: {reason}"
            raise SafetyFault(self._last_fault)
        if not self.motion_allowed():
            self.require_motion("cycle_start")

    def latch_estop(self) -> None:
        self.inputs = InterlockInputs(
            estop_latched=True,
            door_closed=self.inputs.door_closed,
            gripper_pressure_ok=False,
            light_curtain_clear=self.inputs.light_curtain_clear,
            technician_enable=False,
            drive_power_ok=self.inputs.drive_power_ok,
        )
        self._fault_latched = True
        self._last_fault = "E-stop latched"

    def clear_estop(self, technician_key: bool = True) -> bool:
        if not technician_key:
            return False
        self.inputs = InterlockInputs(
            estop_latched=False,
            door_closed=self.inputs.door_closed,
            gripper_pressure_ok=True,
            light_curtain_clear=self.inputs.light_curtain_clear,
            technician_enable=True,
            drive_power_ok=self.inputs.drive_power_ok,
        )
        self._fault_latched = False
        self._last_fault = ""
        return True

    def snapshot(self) -> dict:
        return {
            "motion_allowed": self.motion_allowed(),
            "fault_latched": self._fault_latched,
            "last_fault": self._last_fault,
            "inputs": self.inputs.__dict__,
            "cycles_last_hour": len(self.duty._cycle_times),
        }
