"""
Command line entry point for MuscleMate.
"""

from __future__ import annotations

import argparse
import logging
from contextlib import suppress
from dataclasses import replace
from pathlib import Path
from typing import Optional

from .config import Sampling, Speeds, Thresholds, Waypoints
from .runner import run_controller
from .state_machine import SterilizationController
from .trace import TraceWriter
from hardware.adapters import BenchRigAdapter, IntegrationRigAdapter
from hardware.safeguarded_arm import SafeguardedArm
from sim import scripted_cycle

LOGGER = logging.getLogger("musclemate")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="musclemate",
        description="Myoelectric robotic arm with safety interlocks and manufacturing sequences.",
    )
    parser.add_argument("--runtime", type=float, default=Sampling().runtime_s)
    parser.add_argument("--loop-rate", type=float, default=Sampling().loop_hz)
    parser.add_argument("--emg-on", type=float, default=Thresholds().emg_on)
    parser.add_argument("--emg-off", type=float, default=Thresholds().emg_off)
    parser.add_argument("--deadband", type=float, default=Thresholds().deadband)
    parser.add_argument("--debounce", type=float, default=Thresholds().debounce_s)
    parser.add_argument("--cooldown", type=float, default=Thresholds().cooldown_s)
    parser.add_argument("--longpress", type=float, default=Thresholds().longpress_s)
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use scripted EMG inputs to demonstrate a full cycle.",
    )
    parser.add_argument(
        "--adapter",
        choices=["stub", "bench", "integration"],
        default="stub",
        help="Hardware adapter: bench commissioning or integration rig.",
    )
    parser.add_argument(
        "--signoff-id",
        default="",
        help="Bench sign-off id (required for --adapter integration).",
    )
    parser.add_argument(
        "--trace",
        type=Path,
        default=None,
        help="Append JSONL digital-twin trace (state, safety, intents).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    return parser


def resolve_adapter(name: str, signoff_id: str):
    if name == "bench":
        return BenchRigAdapter()
    if name == "integration":
        adapter = IntegrationRigAdapter()
        sid = signoff_id or "BENCH-UNSPECIFIED"
        adapter.set_bench_signoff(sid)
        return adapter
    return None


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.log_level.upper()))

    thresholds = replace(
        Thresholds(),
        emg_on=args.emg_on,
        emg_off=args.emg_off,
        deadband=args.deadband,
        debounce_s=args.debounce,
        cooldown_s=args.cooldown,
        longpress_s=args.longpress,
    )
    sampling = replace(Sampling(), runtime_s=args.runtime, loop_hz=args.loop_rate)

    adapter = resolve_adapter(args.adapter, args.signoff_id)
    trace = TraceWriter(args.trace) if args.trace else None

    if adapter is not None:
        adapter.connect()
        safety = adapter.safety()
        arm = SafeguardedArm(adapter.arm(), safety)
        emg = scripted_cycle() if args.demo else adapter.emg()
        LOGGER.info("Using adapter %s (%s)", adapter.name, adapter.phase.value)
    else:
        from hardware.arm import QArmStub
        from hardware.emg import StaticEMGSource

        safety = None
        arm = QArmStub()
        emg = scripted_cycle() if args.demo else StaticEMGSource()
        if not args.demo:
            LOGGER.warning("Using StaticEMGSource. Use --demo or --adapter bench.")

    controller = SterilizationController(
        arm=arm,
        emg=emg,
        thresholds=thresholds,
        waypoints=Waypoints(),
        speeds=Speeds(),
        safety=safety,
    )

    class Sink:
        def append(self, event) -> None:
            if trace:
                payload = event
                if safety:
                    trace.emit("tick", {"event": payload, "safety": safety.snapshot()})
                else:
                    trace.emit("tick", payload)

    try:
        run_controller(controller, sampling, event_sink=Sink() if trace else None)
    except KeyboardInterrupt:
        LOGGER.info("Interrupted by user.")
    finally:
        with suppress(Exception):
            arm.home()
        if trace:
            trace.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
