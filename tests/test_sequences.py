from hardware.arm import QArmStub
from sequences import MANUFACTURING_VALIDATION, STERILIZATION_AUTOMATION, run_sequence_on_arm
from safety.interlocks import SafetySupervisor


def test_sterilization_sequence_runs():
    arm = QArmStub()
    log = run_sequence_on_arm(arm, STERILIZATION_AUTOMATION, SafetySupervisor())
    assert len(log) == STERILIZATION_AUTOMATION.step_count()
    assert any(e["kind"] == "MOVE" for e in log)
    assert arm.pose == (0, 0, 0, 0, 0, 0)


def test_manufacturing_sequence_records_cycle():
    arm = QArmStub()
    safety = SafetySupervisor()
    run_sequence_on_arm(arm, MANUFACTURING_VALIDATION, safety)
    assert len(safety.duty._cycle_times) == 1
