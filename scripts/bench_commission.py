#!/usr/bin/env python3
"""Technician-led bench commissioning before integration handoff."""

from __future__ import annotations

import json
import sys

from hardware.adapters import BenchRigAdapter
from sequences import MANUFACTURING_VALIDATION, run_sequence_on_arm


def main() -> int:
    adapter = BenchRigAdapter()
    adapter.connect()
    probe = adapter.run_bench_motion_probe()
    arm = adapter.arm()
    safety = adapter.safety()
    seq_log = run_sequence_on_arm(arm, MANUFACTURING_VALIDATION, safety)
    report = adapter.commissioning_report()
    report["bench_probe"] = probe
    report["validation_sequence_steps"] = len(seq_log)
    print(json.dumps(report, indent=2))
    print("\nBench commissioning complete. Record signoff_id in integration adapter.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
