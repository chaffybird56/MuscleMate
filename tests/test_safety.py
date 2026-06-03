import pytest

from safety.interlocks import DutyCyclePolicy, InterlockInputs, SafetySupervisor, SafetyFault


def test_motion_blocked_when_estop_latched():
    sup = SafetySupervisor(InterlockInputs(estop_latched=True))
    assert not sup.motion_allowed()
    with pytest.raises(SafetyFault):
        sup.require_motion()


def test_duty_cycle_min_gap():
    duty = DutyCyclePolicy(min_cycle_gap_s=10.0)
    duty.record_cycle_complete()
    ok, reason = duty.allow_new_cycle()
    assert not ok
    assert "min_cycle_gap" in reason


def test_clear_estop_requires_technician_key():
    sup = SafetySupervisor()
    sup.latch_estop()
    assert not sup.clear_estop(technician_key=False)
    assert sup.clear_estop(technician_key=True)
    assert sup.motion_allowed()
