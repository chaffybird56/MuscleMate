#!/usr/bin/env python3
"""Run a versioned Python motion sequence (manufacturing / sterilization)."""

from __future__ import annotations

import argparse
import json
import sys

from hardware.adapters import BenchRigAdapter, IntegrationRigAdapter
from hardware.safeguarded_arm import SafeguardedArm
from sequences import MANUFACTURING_VALIDATION, STERILIZATION_AUTOMATION, run_sequence_on_arm

SEQUENCES = {
    "sterilization": STERILIZATION_AUTOMATION,
    "manufacturing": MANUFACTURING_VALIDATION,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run MuscleMate motion sequence")
    parser.add_argument(
        "--sequence",
        choices=list(SEQUENCES.keys()),
        default="sterilization",
    )
    parser.add_argument("--adapter", choices=["bench", "integration"], default="bench")
    parser.add_argument("--signoff-id", default="BENCH-LOCAL-001")
    args = parser.parse_args(argv)

    if args.adapter == "bench":
        adapter = BenchRigAdapter()
    else:
        adapter = IntegrationRigAdapter()
        adapter.set_bench_signoff(args.signoff_id)

    adapter.connect()
    safety = adapter.safety()
    arm = SafeguardedArm(adapter.arm(), safety)
    seq = SEQUENCES[args.sequence]
    log = run_sequence_on_arm(arm, seq, safety)
    out = {
        "sequence": seq.name,
        "version": seq.version,
        "adapter": adapter.commissioning_report(),
        "steps_executed": len(log),
        "motion_records": len(arm.motion_log),
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
