"""
Command line entry point for MuscleMate.
"""

from __future__ import annotations

import argparse
import logging
from contextlib import suppress
from dataclasses import replace
from typing import Optional

from .config import Sampling, Speeds, Thresholds, Waypoints
from .runner import run_controller
from .state_machine import SterilizationController
from hardware.arm import ArmInterface, QArmStub
from hardware.emg import EMGReader, StaticEMGSource
from sim import scripted_cycle

LOGGER = logging.getLogger("musclemate")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="musclemate",
        description="Myoelectric-controlled robotic sterilization demo.",
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
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    return parser


def create_arm() -> ArmInterface:
    LOGGER.warning("Using QArmStub. Replace with hardware binding for live runs.")
    return QArmStub()


def create_emg_source(demo: bool) -> EMGReader:
    if demo:
        return scripted_cycle()
    LOGGER.warning("Using StaticEMGSource. Provide a hardware reader for production.")
    return StaticEMGSource()


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

    arm = create_arm()
    emg = create_emg_source(args.demo)

    controller = SterilizationController(
        arm=arm,
        emg=emg,
        thresholds=thresholds,
        waypoints=Waypoints(),
        speeds=Speeds(),
    )

    try:
        run_controller(controller, sampling)
    except KeyboardInterrupt:
        LOGGER.info("Interrupted by user.")
    finally:
        with suppress(Exception):
            arm.home()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

